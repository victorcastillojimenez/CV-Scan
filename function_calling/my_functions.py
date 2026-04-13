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
        JSON string con las ofertas encontradas en formato estructurado.

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

    logger.info("🔍 Buscando ofertas: '%s'", query)

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FunctionCallingError(f"Error en búsqueda Serper: {exc}") from exc

    resultados = response.json()

    # Extraer y formatear resultados con estructura detallada
    ofertas = []
    for i, item in enumerate(resultados.get("organic", [])[:5], 1):
        titulo = item.get("title", "Sin título")
        url_oferta = item.get("link", "")
        snippet = item.get("snippet", "")
        
        # Extracto del snippet para descripción
        descripcion = snippet[:200] + "..." if len(snippet) > 200 else snippet
        
        # Extraer nombre de empresa del título o snippet (simplificado)
        empresa = titulo.split(" - ")[-1] if " - " in titulo else "Empresa"
        
        oferta_estructurada = {
            "job_id": f"JOB_{i:05d}",
            "titulo": titulo,
            "empresa": empresa.strip(),
            "ubicacion": ubicacion,
            "modalidad": modalidad.capitalize(),
            "descripcion_corta": descripcion,
            "url": url_oferta,
            "relevancia": "Alta" if any(palabra in titulo.lower() for palabra in rol.lower().split()) else "Media",
        }
        
        ofertas.append(oferta_estructurada)

    logger.info("✅ Encontradas %d ofertas para '%s'", len(ofertas), rol)

    return json.dumps(ofertas, ensure_ascii=False, indent=2)


def generar_carta_presentacion(
    empresa: str, puesto: str, tono: str, cv_path: str
) -> str:
    """Genera carta de presentación lista para copiar/pegar usando datos del CV.

    Lee el CV, extrae datos y consulta el RAG para preparar una carta
    completa, personalizada y lista para enviar.

    Args:
        empresa: Nombre de la empresa destino.
        puesto: Puesto al que se postula.
        tono: Tono deseado (formal, semiformal, creativo).
        cv_path: Ruta al archivo PDF del CV.

    Returns:
        String con carta estructurada, contacto y contexto para el LLM.
    """
    # 1. Leer CV completo
    texto_cv = _leer_pdf(cv_path)

    # 2. Extraer datos estructurados del CV
    datos_cv = {}
    try:
        from function_calling.cv_extractor import ExtractorCV
        extractor = ExtractorCV()
        datos_cv = extractor.extraer_datos_estructurados(texto_cv)
        logger.info(f"✓ Datos del candidato extraídos: {datos_cv.get('nombre', 'N/A')}")
    except Exception as exc:
        logger.warning(f"No se pudieron extraer datos estructurados: {exc}")

    # 3. Consultar RAG para buenas prácticas
    contexto_rag = ""
    try:
        from core.rag import consultar_rag, inicializar_coleccion
        coleccion = inicializar_coleccion()
        contexto_rag = consultar_rag(
            f"carta de presentación {tono} para {puesto} en {empresa}",
            coleccion,
        )
    except Exception:
        pass

    # 4. Extraer datos clave del candidato
    nombre = datos_cv.get('nombre', 'Candidato')
    email = datos_cv.get('email', 'email@ejemplo.com')
    telefono = datos_cv.get('telefono', '+34 XXX XXX XXX')
    ubicacion = datos_cv.get('ubicacion', 'Ubicación')
    titulo_pro = datos_cv.get('titulo_profesional', 'Profesional')
    experiencia_anos = datos_cv.get('experiencia_anos', 0)
    
    # Extractar habilidades y tecnologías
    skills = datos_cv.get('lenguajes_programacion', [])
    if not skills:
        skills = datos_cv.get('habilidades', [])
    skills_str = ', '.join(skills[:5]) if skills else 'ver CV'
    
    # Extractar experiencia principal
    experiencia = datos_cv.get('experiencia', [])
    exp_principal = ""
    if experiencia:
        exp = experiencia[0]
        exp_principal = f"{exp.get('puesto', 'Puesto')} en {exp.get('empresa', 'Empresa')} ({exp.get('duracion', 'duración')})"

    # 5. Construir contexto para el LLM
    contexto = f"""
📋 DATOS PERSONALES DEL CANDIDATO (COPY-PASTE READY):
═════════════════════════════════════════════════════
Nombre: {nombre}
Email: {email}
Teléfono: {telefono}
Ubicación: {ubicacion}
Perfil: {titulo_pro}

💼 EXPERIENCIA:
Años: {experiencia_anos}
Última posición: {exp_principal}
Habilidades principales: {skills_str}

🎯 DETALLES DE LA POSTULACIÓN:
═════════════════════════════
Empresa objetivo: {empresa}
Puesto: {puesto}
Tono deseado: {tono}

📝 INSTRUCCIONES PARA LA CARTA:
═════════════════════════════
1. Usa EXACTAMENTE estos datos del candidato (no cambies nombres, email, teléfono):
   - Nombre completo: {nombre}
   - Email: {email}
   - Teléfono: {telefono}
   
2. La carta debe:
   ✅ Ser específica para {empresa} (investiga y menciona algo de la empresa)
   ✅ Adaptar experiencia a {puesto}
   ✅ Usar tono {tono}
   ✅ Incluir datos reales del CV: {titulo_pro}, {experiencia_anos} años, {skills_str}
   ✅ Ser completa, lista para copiar y pegar directamente
   ✅ Incluir firma formal con contacto
   
3. Estructura esperada:
   - Saludo (formal o según tono)
   - Párrafo de introducción (quién eres, por qué te interesa)
   - Párrafo de experiencia (destaca logros relevantes)
   - Párrafo de motivación (por qué quieres esta empresa)
   - Llamada a la acción
   - Despedida con nombre completo y contacto

📄 CV DEL CANDIDATO (para referencia):
{texto_cv[:2000]}

{"🎓 BUENAS PRÁCTICAS DE CARTAS:" + contexto_rag if contexto_rag else ""}
"""

    return contexto


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
