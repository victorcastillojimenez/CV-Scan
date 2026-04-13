"""
Orquestador principal de Function Calling para CV SCAN AI.

Implementa el flujo completo siguiendo el patrón del profesor:
1. Enviar mensaje + tools al LLM  → el LLM decide qué funciones invocar
2. Ejecutar las funciones reales   → acceder a recursos externos
3. Enviar resultados + schema      → obtener respuesta estructurada (JSON)

Equivalente Python de manage-incidence.js del profesor.
"""

import json
import logging
import os
from typing import Any

from openai import OpenAI

from function_calling.tools import TOOLS
from function_calling.schemas import SCHEMA_MAP
from function_calling.my_functions import (
    FunctionCallingError,
    buscar_ofertas_empleo,
    generar_carta_presentacion,
    extraer_datos_cv,
    _leer_pdf,
)
from function_calling.cv_extractor import ExtractorCV

# =============================================
#  Configuración
# =============================================

MODEL_NAME = "gpt-4o-mini"

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = (
    "Eres un experto en redacción de cartas de presentación y búsqueda de empleo. "
    "Tienes acceso a herramientas para: buscar ofertas reales, generar cartas profesionales, "
    "y extraer datos del CV.\n\n"
    "📋 INFORMACIÓN DEL CANDIDATO:\n"
    "{contexto_cv}\n\n"
    "⚙️ INSTRUCCIONES CRÍTICAS:\n"
    "- Cuando generes cartas: USA EXACTAMENTE los datos personales proporcionados\n"
    "- Las cartas deben ser COMPLETAS y LISTAS para copiar/pegar en email\n"
    "- Incluye saludo, introducción, experiencia relevante, motivación y cierre\n"
    "- En búsquedas: Estructura cada oferta con job_id, sector, funciones, perfil buscado y beneficios\n"
    "- Personaliza siempre usando datos reales del candidato: nombre, experiencia, habilidades\n"
    "- Usa siempre las herramientas cuando el usuario las solicite."
)


# =============================================
#  Funciones auxiliares
# =============================================


def _build_input(message: str, cv_path: str) -> list[dict[str, str]]:
    """Construye los mensajes de entrada (developer + user) con contexto del CV.

    Args:
        message: Mensaje del usuario.
        cv_path: Ruta al CV para extraer datos.

    Returns:
        Lista de mensajes con roles 'developer' y 'user'.
    """
    # Extraer contexto del CV automáticamente
    contexto_cv = ""
    try:
        texto_cv = _leer_pdf(cv_path)
        extractor = ExtractorCV()
        contexto_cv = extractor.obtener_contexto_cv(texto_cv)
        logger.info(f"✓ Contexto del CV extraído exitosamente")
    except Exception as e:
        logger.warning(f"No se pudo extraer contexto del CV: {e}")
        contexto_cv = f"CV disponible en: {cv_path}"

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(contexto_cv=contexto_cv)

    return [
        {
            "role": "developer",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": message,
        },
    ]


def _handle_function_call(
    name: str, args: dict[str, Any], cv_path: str
) -> str:
    """Enruta la llamada del LLM a la función real correspondiente.

    Args:
        name: Nombre de la función invocada por el LLM.
        args: Argumentos extraídos del JSON del LLM.
        cv_path: Ruta al CV (inyectada por el orquestador).

    Returns:
        Resultado de la función como string.

    Raises:
        FunctionCallingError: Si la función es desconocida.
    """
    if name == "buscar_ofertas_empleo":
        return buscar_ofertas_empleo(**args)
    elif name == "generar_carta_presentacion":
        return generar_carta_presentacion(cv_path=cv_path, **args)
    elif name == "extraer_datos_cv":
        # El orquestador inyecta la ruta real del CV
        return extraer_datos_cv(ruta_cv=cv_path)
    else:
        raise FunctionCallingError(f"Función desconocida: {name}")


def _get_structured_data(
    client: OpenAI,
    input_data: list[dict[str, str]],
    previous_response: Any,
    schema_name: str,
    schema: dict,
) -> dict[str, Any]:
    """Segunda llamada al LLM: obtiene respuesta estructurada.

    Equivalente a la función getStructuredData() del profesor.

    Args:
        client: Cliente OpenAI inicializado.
        input_data: Lista de function_call_output para el LLM.
        previous_response: Respuesta de la primera llamada (para obtener el id).
        schema_name: Nombre del schema JSON.
        schema: Diccionario con el JSON Schema.

    Returns:
        Diccionario con la respuesta estructurada del LLM.
    """
    response = client.responses.create(
        model=MODEL_NAME,
        input=input_data,
        text={
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "schema": schema,
                "strict": True,
            }
        },
        previous_response_id=previous_response.id,
    )
    return json.loads(response.output_text)


# =============================================
#  Función principal (punto de entrada)
# =============================================


def gestionar_cv(message: str, cv_path: str) -> dict[str, Any]:
    """Orquesta el flujo completo de Function Calling.

    1. Envía el mensaje del usuario + herramientas al LLM.
    2. El LLM decide qué funciones invocar y con qué argumentos.
    3. Se ejecutan las funciones reales (Serper, PDF, RAG).
    4. Se envían los resultados al LLM con un JSON Schema para
       obtener una respuesta estructurada.

    Args:
        message: Mensaje del usuario (ej: "Busca ofertas de Data Analyst").
        cv_path: Ruta al archivo PDF del CV del candidato.

    Returns:
        Diccionario con la respuesta estructurada del LLM.

    Raises:
        FunctionCallingError: Si falta la API key o hay error en el proceso.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise FunctionCallingError(
            "OPENAI_API_KEY no configurada. Añádela al archivo .env"
        )

    client = OpenAI(api_key=api_key)
    input_messages = _build_input(message, cv_path)

    # ── 1ª LLAMADA: LLM decide qué funciones usar ──────────────
    logger.info("Enviando mensaje al LLM con %d herramientas", len(TOOLS))

    response = client.responses.create(
        model=MODEL_NAME,
        input=input_messages,
        tools=TOOLS,
    )

    # ── PROCESAR LLAMADAS A FUNCIONES ───────────────────────────
    new_input: list[dict[str, str]] = []
    last_function_name: str | None = None
    funciones_invocadas: list[dict[str, Any]] = []

    for item in response.output:
        if item.type != "function_call":
            continue

        name = item.name
        args = json.loads(item.arguments)

        logger.info("🔧 LLM invocó: %s(%s)", name, args)

        result = _handle_function_call(name, args, cv_path)
        last_function_name = name
        
        # Registrar función invocada
        funciones_invocadas.append({
            "nombre": name,
            "argumentos": args,
            "resultado_chars": len(result)
        })

        logger.info("✓ Resultado de %s: %d caracteres", name, len(result))

        new_input.append({
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": result,
        })

    # Si el LLM no invocó ninguna función, devolver texto directo
    if not last_function_name:
        logger.warning("⚠️ El LLM no invocó ninguna función")
        return {
            "respuesta_directa": response.output_text,
            "funciones_invocadas": [],
        }

    # ── 2ª LLAMADA: Respuesta estructurada con JSON Schema ─────
    schema_name, schema = SCHEMA_MAP[last_function_name]
    logger.info("📊 Solicitando respuesta estructurada: %s", schema_name)

    resultado = _get_structured_data(
        client, new_input, response, schema_name, schema
    )
    
    # Agregar información de funciones invocadas al resultado
    resultado["_funciones_invocadas"] = funciones_invocadas
    
    return resultado
