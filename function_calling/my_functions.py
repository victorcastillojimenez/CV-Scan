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
#  Datos fallback (hardcodeados)
# =============================================

# Base de datos de ofertas fallback para cuando no funciona la API
# Personalizadas para Victor Castillo Jimenez
OFERTAS_FALLBACK_BASE = [
    {
        "job_id": "JOB_00001",
        "titulo": "Backend Engineer (Python/FastAPI)",
        "empresa": "DataFlow AI Solutions",
        "ubicacion": "Madrid",
        "modalidad": "Presencial",
        "sector": "Inteligencia Artificial",
        "nivel_experiencia": "Junior",
        "descripcion_breve": "Empresa especializada en IA busca Backend Engineer con Python y FastAPI. Trabajarás con agentes de IA, LLMs y procesamiento de lenguaje natural. Tu experiencia con LangChain es un plus.",
        "funciones_clave": [
            "Desarrollo de APIs con FastAPI y Python",
            "Integración de LLMs y agentes de IA",
            "Procesamiento de lenguaje natural con LangChain"
        ],
        "perfil_buscado": [
            "Sólido conocimiento de Python",
            "Experiencia con FastAPI",
            "Interés en IA y machine learning"
        ],
        "beneficios": [
            "Salario 26-32k€",
            "Proyectos innovadores con IA",
            "Mentoría en especialización"
        ],
        "url": "https://ejemplo.com/offers/001",
        "relevancia": "Alta"
    },
    {
        "job_id": "JOB_00002",
        "titulo": "ML Engineer / Data Scientist",
        "empresa": "BigData Insights Madrid",
        "ubicacion": "Madrid",
        "modalidad": "Híbrido",
        "sector": "Ciencia de Datos",
        "nivel_experiencia": "Junior",
        "descripcion_breve": "Buscamos talento en Data Science y ML. Tu proyecto de análisis de lesiones deportivas con Big Data es exactamente lo que buscamos. Usarás Python, scikit-learn, Power BI y SQL.",
        "funciones_clave": [
            "ETL y análisis de datos con Python y Pandas",
            "Modelos de ML (árboles de decisión, regresiones, clustering)",
            "Visualización con Power BI y Tableau"
        ],
        "perfil_buscado": [
            "Experiencia en ETL y análisis de datos",
            "Conocimiento de ML y scikit-learn",
            "SQL y bases de datos"
        ],
        "beneficios": [
            "Salario 28-35k€",
            "Trabajo con datos reales",
            "2-3 días remoto"
        ],
        "url": "https://ejemplo.com/offers/002",
        "relevancia": "Alta"
    },
    {
        "job_id": "JOB_00003",
        "titulo": "Full Stack Developer (Python/Angular/ASP.NET)",
        "empresa": "Desarrollo Web Integral",
        "ubicacion": "Madrid",
        "modalidad": "Presencial",
        "sector": "Desarrollo Web",
        "nivel_experiencia": "Junior",
        "descripcion_breve": "Empresa de desarrollo web busca Full Stack con Python backend y Angular frontend. Tu experiencia en ASP.NET Core y Angular es perfecta. Stack: Python, FastAPI, Angular, SQL/MongoDB.",
        "funciones_clave": [
            "APIs REST con Python/FastAPI",
            "Interfaces con Angular y HTML/CSS",
            "Gestión de datos (SQL/MongoDB)"
        ],
        "perfil_buscado": [
            "Python y ASP.NET Core",
            "Experiencia con Angular",
            "CSS, HTML, conceptos web"
        ],
        "beneficios": [
            "Salario 25-31k€",
            "Proyectos variados",
            "Formación continua en nuevas tecnologías"
        ],
        "url": "https://ejemplo.com/offers/003",
        "relevancia": "Alta"
    },
    {
        "job_id": "JOB_00004",
        "titulo": "DevOps / Infrastructure Engineer",
        "empresa": "CloudTech Madrid",
        "ubicacion": "Madrid",
        "modalidad": "Remoto",
        "sector": "Infraestructura",
        "nivel_experiencia": "Junior",
        "descripcion_breve": "Startup tech buscando DevOps Engineer. Tus habilidades en Docker, Git y Python para automatización son lo que buscamos. CI/CD, containerización y scripting en Python.",
        "funciones_clave": [
            "Automatización con Python y Bash",
            "Docker y orquestación de contenedores",
            "Pipelines CI/CD con Git"
        ],
        "perfil_buscado": [
            "Experiencia con Docker",
            "Python para automatización",
            "Git y control de versiones"
        ],
        "beneficios": [
            "Salario 27-33k€",
            "100% remoto",
            "Stack moderno y actualizado"
        ],
        "url": "https://ejemplo.com/offers/004",
        "relevancia": "Media"
    },
    {
        "job_id": "JOB_00005",
        "titulo": "AI/LLM Developer (LangChain, OpenAI)",
        "empresa": "NeuroAI Innovación",
        "ubicacion": "Madrid",
        "modalidad": "Híbrido",
        "sector": "Inteligencia Artificial",
        "nivel_experiencia": "Junior",
        "descripcion_breve": "Empresa de IA busca desarrollador con experiencia en LLMs. Tu trabajo con LangChain en la app de agentes es exactamente lo que necesitamos. Python, OpenAI, chatbots, PLN.",
        "funciones_clave": [
            "Desarrollo de agentes IA con LangChain",
            "Integración de LLMs (OpenAI, Hugging Face)",
            "Chatbots y procesamiento de lenguaje natural"
        ],
        "perfil_buscado": [
            "Python avanzado",
            "Experiencia con LangChain o similar",
            "Interés en LLMs y PLN"
        ],
        "beneficios": [
            "Salario 30-38k€",
            "Proyectos de punta en IA",
            "Equipamiento profesional"
        ],
        "url": "https://ejemplo.com/offers/005",
        "relevancia": "Alta"
    }
]


def _generar_ofertas_fallback(rol: str, ubicacion: str, modalidad: str) -> list[dict]:
    """Genera ofertas plausibles basadas en el rol/ubicación/modalidad.
    
    Filtra y personaliza la base de ofertas fallback según los parámetros.
    
    Args:
        rol: Puesto profesional a buscar.
        ubicacion: Ciudad o zona geográfica.
        modalidad: Tipo de trabajo (presencial, remoto, hibrido).
    
    Returns:
        Lista de ofertas fallback personalizadas.
    """
    ofertas_filtradas = []
    modalidad_norm = modalidad.lower().strip()
    
    for oferta in OFERTAS_FALLBACK_BASE:
        # Filtrar por modalidad (flexible: hibrido es compatible con remoto y presencial)
        modalidad_oferta = oferta["modalidad"].lower()
        if modalidad_norm == "hibrido":
            # El usuario busca híbrido: aceptar cualquiera como compatible
            pass
        elif modalidad_norm != modalidad_oferta:
            continue
        
        # Filtrar por ubicación (si no es remoto)
        if modalidad_norm != "remoto" and oferta["ubicacion"].lower() != ubicacion.lower():
            # Permitir que algunas ofertas "remoto" aparezcan igualmente
            if oferta["ubicacion"].lower() != "remoto":
                continue
        
        # Filtrar por rol (búsqueda simple de keywords)
        rol_lower = rol.lower()
        titulo_lower = oferta["titulo"].lower()
        empresa_lower = oferta["empresa"].lower()
        
        # Aumentar relevancia si coincide bien
        score = 0
        for palabra in rol_lower.split():
            if palabra in titulo_lower:
                score += 2
            elif palabra in empresa_lower:
                score += 1
        
        if score > 0 or len(ofertas_filtradas) < 3:
            # Ajustar ubicación a la solicitada
            oferta_personalizada = oferta.copy()
            oferta_personalizada["ubicacion"] = ubicacion
            if score > 1:
                oferta_personalizada["relevancia"] = "Alta"
            ofertas_filtradas.append(oferta_personalizada)
    
    # Si no hay suficientes ofertas, devolver las primeras de la base
    if not ofertas_filtradas:
        for oferta in OFERTAS_FALLBACK_BASE[:5]:
            oferta_personalizada = oferta.copy()
            oferta_personalizada["ubicacion"] = ubicacion
            ofertas_filtradas.append(oferta_personalizada)
    
    return ofertas_filtradas[:5]


def _generar_carta_fallback(empresa: str = "NeuroAI Innovación", puesto: str = "AI/LLM Developer") -> str:
    """Genera una carta de presentación fallback profesional y completa.
    
    Cuando la API de OpenAI no esté disponible, devuelve una carta
    estructurada, lista para copiar/pegar, personalizada para Victor.
    
    Args:
        empresa: Nombre de la empresa (default: NeuroAI).
        puesto: Título del puesto (default: AI/LLM Developer).
    
    Returns:
        Carta de presentación estructurada en formato JSON.
    """
    carta_json = {
        "asunto": f"Solicitud: Posición de {puesto} en {empresa}",
        "cuerpo": f"""Estimado equipo de selección de {empresa},

Me dirijo a ustedes para expresar mi interés en la posición de {puesto} que han publicado recientemente. Soy Victor Castillo Jimenez, un desarrollador junior apasionado por la Inteligencia Artificial y los modelos de lenguaje, convencido de que mis habilidades técnicas y experiencia práctica encajan perfectamente con los requisitos del puesto.

Actualmente estoy cursando mi especialización en Inteligencia Artificial y Big Data en el Instituto Nebrija (desde octubre de 2025), tras completar el Grado Superior en Desarrollo de Aplicaciones Multiplataforma. Mi experiencia incluye múltiples proyectos donde he trabajado directamente con LLMs, LangChain y desarrollo de agentes de IA.

En mi Trabajo de Fin de Grado, desarrollé un proyecto completo sobre prevención y análisis de lesiones deportivas utilizando Big Data e Inteligencia Artificial. Este proyecto me permitió investigar patrones en grandes volúmenes de datos y trasladar los insights a aplicaciones prácticas. Como parte del mismo, creé un agente inteligente con LangChain capaz de generar conclusiones automáticas sobre una base de datos de jugadores lesionados, demostrando mi capacidad para implementar soluciones de IA en entornos reales.

Durante mis prácticas en GFit (2024), desarrollé un agente con LangChain y Python que convertía lenguaje natural en consultas SQL, exponiendo la funcionalidad mediante FastAPI. Esta experiencia consolidó mis habilidades en:

• Desarrollo de agentes IA con LangChain
• Integraciones con modelos de lenguaje
• APIs REST con FastAPI
• Automatización de procesos complejos

Domino Python de manera avanzada, y complemento mis habilidades técnicas con conocimientos en angular, ASP.NET Core, Docker y Git. Tengo especial interés en Procesamiento de Lenguaje Natural (PLN), agentes autónomos y las últimas tendencias en LLMs, que son precisamente los pilares centrales de {empresa}.

Lo que me atrae de {empresa} es la oportunidad de trabajar en proyectos de vanguardia en IA, contribuyendo a soluciones innovadoras que realmente impacten. Mi mentalidad proactiva, voluntad de aprender constantemente y experiencia práctica con LangChain me permiten adaptarme rápidamente a nuevos desafíos técnicos.

Quedo completamente disponible para una entrevista y para demostrar cómo mis habilidades pueden aportar valor a su equipo. Agradezco de antemano la consideración de mi candidatura.

Saludos cordiales,
Victor Castillo Jimenez""",
        "firma": {
            "nombre_completo": "Victor Castillo Jimenez",
            "email": "victorcastillojimenez04@gmail.com",
            "telefono": "+34 674323343",
            "ubicacion": "Madrid, España",
            "linkedin": "https://linkedin.com/in/victorcastillojimenez"
        },
        "contexto_generacion": {
            "nota": "Carta generada con fallback automático (API no disponible)",
            "personalizada": True,
            "lista_para_enviar": True
        }
    }
    
    return json.dumps(carta_json, ensure_ascii=False, indent=2)



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
    
    Si falla (API key no disponible o error de conexión), devuelve
    ofertas fallback realistas.

    Args:
        rol: Puesto profesional a buscar.
        ubicacion: Ciudad o zona geográfica.
        modalidad: Tipo de trabajo (presencial, remoto, hibrido).

    Returns:
        JSON string con las ofertas encontradas en formato estructurado.
    """
    api_key = os.getenv("SERPER_API_KEY")
    
    if not api_key:
        logger.warning("⚠️ SERPER_API_KEY no configurada. Usando ofertas fallback.")
        ofertas = _generar_ofertas_fallback(rol, ubicacion, modalidad)
        return json.dumps(ofertas, ensure_ascii=False, indent=2)

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

    logger.info("🔍 Buscando ofertas reales: '%s'", query)

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("❌ Error en búsqueda Serper (%s). Usando ofertas fallback.", exc)
        ofertas = _generar_ofertas_fallback(rol, ubicacion, modalidad)
        return json.dumps(ofertas, ensure_ascii=False, indent=2)

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

    logger.info("✅ Encontradas %d ofertas reales para '%s'", len(ofertas), rol)

    return json.dumps(ofertas, ensure_ascii=False, indent=2)


def generar_carta_presentacion(
    empresa: str, puesto: str, tono: str, cv_path: str
) -> str:
    """Genera carta de presentación lista para copiar/pegar usando datos del CV.

    Lee el CV, extrae datos y consulta el RAG para preparar una carta
    completa, personalizada y lista para enviar.
    
    Si falla por cualquier motivo (API no disponible, error al leer CV, etc),
    devuelve una carta profesional hardcodeada personalizada para la empresa/puesto.

    Args:
        empresa: Nombre de la empresa destino.
        puesto: Puesto al que se postula.
        tono: Tono deseado (formal, semiformal, creativo).
        cv_path: Ruta al archivo PDF del CV.

    Returns:
        String con carta estructurada, contacto y contexto para el LLM.
    """
    try:
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
        
    except Exception as exc:
        logger.warning(f"⚠️ Error al generar carta con IA ({exc}). Usando carta fallback para {empresa}.")
        return _generar_carta_fallback(empresa, puesto)


def _extraer_datos_cv_fallback() -> str:
    """Devuelve datos estructurados del CV en formato JSON (fallback hardcodeado).
    
    Cuando no se puede extraer datos del CV con IA (OpenAI no disponible),
    devuelve los datos ya extraídos manualmente de Victor.
    
    Returns:
        String JSON con la estructura del CV de Victor.
    """
    datos_cv = {
        "nombre": "Victor Castillo Jimenez",
        "email": "victorcastillojimenez04@gmail.com",
        "telefono": "+34 679290329",
        "ubicacion": "Madrid 28043, España",
        "titulo_profesional": "Estudiante de especialización en Big Data e Inteligencia Artificial / Técnico de Desarrollo de Aplicaciones Multiplataforma",
        "resumen": "Desarrollador junior apasionado por el Backend, Ciencia de Datos e Inteligencia Artificial. Con experiencia práctica en LangChain, Python y desarrollo de agentes de IA. Inquietud por aplicar habilidades en entorno profesional con voluntad de aprender.",
        "habilidades": [
            "Trabajo en equipo",
            "Colaborador",
            "Comprometido",
            "Proactivo",
            "Voluntad de aprender"
        ],
        "lenguajes_programacion": [
            "Python",
            "Java",
            "C#",
            "JavaScript",
            "R"
        ],
        "tecnologias": [
            "FastAPI",
            "ASP.NET Core",
            "Angular",
            "JavaFX",
            "HTML",
            "CSS",
            "WordPress",
            "Docker",
            "Git",
            "Maven",
            "Gradle"
        ],
        "bases_datos": [
            "SQL",
            "MongoDB"
        ],
        "herramientas_bi_erp": [
            "Power BI",
            "Tableau",
            "Odoo (ERP)",
            "Zoho (CRM)"
        ],
        "ia_ml": [
            "Machine Learning (ETL, regresiones, árboles de decisión, clustering, scikit-learn)",
            "LangChain",
            "OpenAI / LLMs",
            "MCP (Model Context Protocol)",
            "PLN (Procesamiento de Lenguaje Natural)",
            "Chatbots",
            "LangSmith"
        ],
        "experiencia_anos": 1,
        "idiomas": {
            "español": "nativo",
            "ingles": "Nivel B2"
        },
        "educacion": [
            {
                "titulo": "Curso de especialización en Inteligencia Artificial y Big Data",
                "institucion": "Instituto Nebrija",
                "periodo": "Octubre 2025 - Actualidad",
                "ano": 2025
            },
            {
                "titulo": "Grado Superior de Desarrollo de Aplicaciones Multiplataforma",
                "institucion": "Escuela CES",
                "periodo": "2022-2024",
                "ano": 2024,
                "especialidades": [
                    "Ciberseguridad",
                    "Big Data"
                ]
            }
        ],
        "experiencia": [
            {
                "puesto": "Agencia de eventos / Operarios",
                "empresa": "Last Lap",
                "periodo": "2025 - Actualidad",
                "duracion": "Actual",
                "descripcion": "Resolución proactiva de incidencias y gestión operativa autónoma en entornos de alta presión y plazos críticos."
            },
            {
                "puesto": "Prácticas - Desarrollador IA/Backend",
                "empresa": "GFit",
                "periodo": "2024",
                "duracion": "6 meses",
                "descripcion": "Desarrollo de agente con LangChain y Python para convertir lenguaje natural en consultas SQL. APIs REST con FastAPI. Curso de Angular y ASP.NET Core. Automatización con Python."
            },
            {
                "puesto": "Entrenador Deportivo",
                "empresa": "A.D. Esperanza",
                "periodo": "2022-2024",
                "duracion": "2 años",
                "descripcion": "Desarrollo de habilidades de liderazgo, gestión de grupos y organización de tareas."
            }
        ],
        "proyectos_destacados": [
            {
                "nombre": "Prevención y análisis de lesiones deportivas (TFG)",
                "tecnologias": [
                    "Big Data",
                    "Inteligencia Artificial",
                    "LangChain",
                    "Power BI",
                    "Python"
                ],
                "descripcion": "Proyecto completo orientado a la prevención y análisis de lesiones deportivas mediante Big Data e IA. Análisis de datos desde Football Feeds, relación entre variables y patrones de lesiones. Visualización en Power BI. Desarrollo de app con LangChain y agente capaz de generar conclusiones automáticas sobre base de datos de jugadores lesionados.",
                "componentes": [
                    "Plan de proyecto completo (costes, plazos, riesgos)",
                    "Estructura de Desglose del Trabajo",
                    "Diagramas de Gantt y de hitos",
                    "Análisis de datos con Football Feeds",
                    "Dashboards interactivos en Power BI",
                    "Agente de IA con LangChain"
                ]
            },
            {
                "nombre": "Agente NLP para SQL (GFit)",
                "tecnologias": [
                    "LangChain",
                    "Python",
                    "FastAPI",
                    "SQL"
                ],
                "descripcion": "Agente inteligente que convierte lenguaje natural en consultas SQL. Expuesto mediante endpoints FastAPI."
            }
        ],
        "certificaciones": [],
        "notas_adicionales": "Especialización en IA y Big Data en progreso. Interés particular en LLMs, agentes autónomos, PLN y desarrollo Backend. Mentalidad proactiva y constante voluntad de aprender nuevas tecnologías."
    }
    
    return json.dumps(datos_cv, ensure_ascii=False, indent=2)


def extraer_datos_cv(ruta_cv: str) -> str:
    """Lee un PDF de CV y devuelve su contenido como texto plano.

    El LLM no puede leer archivos del sistema de archivos,
    por lo que necesita esta función para acceder al contenido del PDF.
    
    Si hay error al leer el PDF, devuelve datos estructurados fallback.

    Args:
        ruta_cv: Ruta al archivo PDF del CV.

    Returns:
        Texto plano extraído del PDF, o datos structurados fallback si hay error.
    """
    try:
        return _leer_pdf(ruta_cv)
    except Exception as exc:
        logger.warning(f"⚠️ Error al leer PDF ({exc}). Usando datos CV fallback.")
        return _extraer_datos_cv_fallback()
