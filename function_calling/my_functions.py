"""
Implementaciones reales de las funciones que el LLM puede invocar.

Cada función accede a recursos que el LLM no puede alcanzar por sí solo:
- buscar_ofertas_empleo  → API de búsqueda web (Serper)
- generar_carta_presentacion → Sistema de archivos (PDF) + Base vectorial (RAG)
- extraer_datos_cv → Sistema de archivos (PDF)
"""

import json
import logging
import os
from pathlib import Path

import requests
from pypdf import PdfReader

logger = logging.getLogger(__name__)


# =============================================
#  Excepciones
# =============================================


class FunctionCallingError(Exception):
    """Error durante la ejecución de una función invocada por el LLM."""


# =============================================
#  Utilidades internas
# =============================================


def _leer_pdf(ruta: str) -> str:
    """Extrae texto plano de un archivo PDF.

    Args:
        ruta: Ruta al archivo PDF.

    Returns:
        Texto extraído concatenado de todas las páginas.

    Raises:
        FunctionCallingError: Si el archivo no existe o no se puede leer.
    """
    path = Path(ruta)

    if not path.exists():
        raise FunctionCallingError(f"Archivo no encontrado: {ruta}")

    if path.suffix.lower() != ".pdf":
        raise FunctionCallingError(f"El archivo no es un PDF: {ruta}")

    try:
        reader = PdfReader(path)
        texto = ""
        for num_pagina, pagina in enumerate(reader.pages, 1):
            contenido = pagina.extract_text()
            if contenido:
                texto += f"\n--- Página {num_pagina} ---\n{contenido}"
        return texto.strip()
    except Exception as exc:
        raise FunctionCallingError(f"Error leyendo PDF {ruta}: {exc}") from exc


# =============================================
#  Funciones principales (invocadas por el LLM)
# =============================================


def buscar_ofertas_empleo(
    rol: str, ubicacion: str, modalidad: str
) -> str:
    """Busca ofertas de empleo reales usando la API de Serper.

    El LLM no puede acceder a internet, por lo que necesita
    esta función como herramienta para obtener datos en tiempo real.

    Args:
        rol: Puesto profesional a buscar.
        ubicacion: Ciudad o zona geográfica.
        modalidad: Tipo de trabajo (presencial, remoto, hibrido).

    Returns:
        JSON string con las ofertas encontradas.

    Raises:
        FunctionCallingError: Si la API key no está configurada o falla la búsqueda.
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        raise FunctionCallingError(
            "SERPER_API_KEY no configurada en el archivo .env"
        )

    query = f"ofertas empleo {rol} {ubicacion} {modalidad} 2026"
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "q": query,
        "gl": "es",
        "hl": "es",
        "num": 5,
    }

    logger.info("Buscando ofertas: '%s'", query)

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FunctionCallingError(f"Error en búsqueda Serper: {exc}") from exc

    resultados = response.json()

    # Extraer resultados orgánicos relevantes
    ofertas = []
    for item in resultados.get("organic", [])[:5]:
        ofertas.append({
            "titulo": item.get("title", "Sin título"),
            "url": item.get("link", ""),
            "descripcion": item.get("snippet", ""),
        })

    logger.info("Encontradas %d ofertas para '%s'", len(ofertas), rol)

    return json.dumps(ofertas, ensure_ascii=False)


def generar_carta_presentacion(
    empresa: str, puesto: str, tono: str, cv_path: str
) -> str:
    """Lee el CV y consulta el RAG para preparar contexto de carta de presentación.

    El LLM no puede leer archivos del disco ni consultar la base vectorial
    ChromaDB, por lo que necesita esta función para obtener ambos contextos.

    Args:
        empresa: Nombre de la empresa destino.
        puesto: Puesto al que se postula.
        tono: Tono deseado (formal, semiformal, creativo).
        cv_path: Ruta al archivo PDF del CV.

    Returns:
        String con el contexto completo (CV + conocimiento experto + datos postulación).
    """
    # Leer CV del candidato
    texto_cv = _leer_pdf(cv_path)

    # Consultar RAG para obtener buenas prácticas sobre cartas
    contexto_rag = ""
    try:
        from core.rag import consultar_rag, inicializar_coleccion

        coleccion = inicializar_coleccion()
        contexto_rag = consultar_rag(
            "buenas prácticas carta de presentación profesional estructura",
            coleccion,
        )
    except ImportError:
        logger.warning("Módulo RAG no disponible, continuando sin contexto experto")
    except Exception as exc:
        logger.warning("Error consultando RAG: %s", exc)

    # Construir contexto completo para el LLM
    partes = [f"CV DEL CANDIDATO:\n{texto_cv[:4000]}"]

    if contexto_rag:
        partes.append(
            f"CONOCIMIENTO EXPERTO sobre cartas de presentación:\n{contexto_rag}"
        )

    partes.append(
        f"DATOS DE LA POSTULACIÓN:\n"
        f"- Empresa: {empresa}\n"
        f"- Puesto: {puesto}\n"
        f"- Tono deseado: {tono}"
    )

    return "\n\n".join(partes)


def extraer_datos_cv(ruta_cv: str) -> str:
    """Lee un PDF de CV y devuelve su contenido como texto plano.

    El LLM no puede leer archivos del sistema de archivos,
    por lo que necesita esta función para acceder al contenido del PDF.

    Args:
        ruta_cv: Ruta al archivo PDF del CV.

    Returns:
        Texto plano extraído del PDF.
    """
    return _leer_pdf(ruta_cv)
