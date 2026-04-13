"""
Schemas JSON para salidas estructuradas (Structured Output).

Cada schema define la estructura exacta que el LLM debe devolver
en la segunda llamada, tras haber ejecutado la función correspondiente.
Compatible con el modo strict de la API Responses de OpenAI.
"""

SCHEMA_OFERTAS: dict = {
    "type": "object",
    "properties": {
        "ofertas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "job_id": {"type": "string", "description": "ID único de la oferta"},
                    "titulo": {"type": "string", "description": "Título del puesto"},
                    "empresa": {"type": "string", "description": "Nombre de la empresa"},
                    "ubicacion": {"type": "string", "description": "Ciudad/región"},
                    "modalidad": {
                        "type": "string",
                        "enum": ["Presencial", "Remoto", "Hibrido"],
                        "description": "Tipo de trabajo"
                    },
                    "sector": {"type": "string", "description": "Sector/industria (ej: Tech, Finance)"},
                    "nivel_experiencia": {
                        "type": "string",
                        "enum": ["Entry Level", "Junior", "Mid", "Senior"],
                        "description": "Nivel requerido"
                    },
                    "descripcion_breve": {
                        "type": "string",
                        "description": "Resumen de la oferta (máx 300 chars)"
                    },
                    "funciones_clave": {
                        "type": "array",
                        "items": {"type": "string"},
                        "maxItems": 3,
                        "description": "3 funciones principales"
                    },
                    "perfil_buscado": {
                        "type": "array",
                        "items": {"type": "string"},
                        "maxItems": 3,
                        "description": "3 requisitos clave"
                    },
                    "beneficios": {
                        "type": "array",
                        "items": {"type": "string"},
                        "maxItems": 3,
                        "description": "3 beneficios principales"
                    },
                    "url": {"type": "string", "description": "Link directo a la oferta"},
                    "relevancia": {
                        "type": "string",
                        "enum": ["Alta", "Media", "Baja"],
                        "description": "Relevancia para el perfil"
                    },
                },
                "required": [
                    "job_id",
                    "titulo",
                    "empresa",
                    "ubicacion",
                    "modalidad",
                    "nivel_experiencia",
                    "descripcion_breve",
                    "url",
                    "relevancia",
                ],
                "additionalProperties": False,
            },
        },
        "resumen": {
            "type": "string",
            "description": "Análisis breve del mercado laboral y tendencias"
        },
    },
    "required": ["ofertas", "resumen"],
    "additionalProperties": False,
}


SCHEMA_CARTA: dict = {
    "type": "object",
    "properties": {
        "asunto": {
            "type": "string",
            "description": "Línea de asunto del email (ej: Solicitud: Posición de Senior Developer en Google)"
        },
        "cuerpo": {
            "type": "string",
            "description": "Cuerpo completo de la carta (introducción, experiencia, motivación, cierre)"
        },
        "firma": {
            "type": "object",
            "properties": {
                "nombre_completo": {"type": "string"},
                "email": {"type": "string"},
                "telefono": {"type": "string"},
                "ubicacion": {"type": "string"},
                "linkedin": {"type": "string", "description": "URL de LinkedIn (si aplica)"}
            },
            "required": ["nombre_completo", "email", "telefono"],
            "description": "Datos de firma con contacto ready-to-use"
        },
        "texto_completo_email": {
            "type": "string",
            "description": "Carta completa formateada lista para copiar y pegar en email"
        },
        "consejos_envio": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 3,
            "description": "3 consejos sobre cómo enviar esta carta"
        },
        "tono_detectado": {
            "type": "string",
            "enum": ["formal", "semiformal", "creativo"],
            "description": "Tono final detectado en la carta"
        },
    },
    "required": ["asunto", "cuerpo", "firma", "texto_completo_email"],
    "additionalProperties": False,
}


SCHEMA_DATOS_CV: dict = {
    "type": "object",
    "properties": {
        "nombre": {"type": "string"},
        "email": {"type": "string"},
        "telefono": {"type": "string"},
        "seniority": {
            "type": "string",
            "enum": ["entry", "junior", "mid", "senior", "lead"],
        },
        "tecnologias": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string"},
                    "nivel": {
                        "type": "string",
                        "enum": ["basico", "intermedio", "avanzado"],
                    },
                },
                "required": ["nombre", "nivel"],
                "additionalProperties": False,
            },
        },
        "idiomas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "idioma": {"type": "string"},
                    "nivel": {"type": "string"},
                },
                "required": ["idioma", "nivel"],
                "additionalProperties": False,
            },
        },
        "experiencia": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "empresa": {"type": "string"},
                    "puesto": {"type": "string"},
                    "duracion": {"type": "string"},
                    "descripcion": {"type": "string"},
                },
                "required": ["empresa", "puesto", "duracion", "descripcion"],
                "additionalProperties": False,
            },
        },
        "educacion": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "institucion": {"type": "string"},
                    "titulo": {"type": "string"},
                    "ano_finalizacion": {"type": "string"},
                },
                "required": ["institucion", "titulo", "ano_finalizacion"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "nombre",
        "email",
        "telefono",
        "seniority",
        "tecnologias",
        "idiomas",
        "experiencia",
        "educacion",
    ],
    "additionalProperties": False,
}


# Mapeo: nombre de función → (nombre del schema, schema)
# Permite que el orquestador seleccione el schema correcto
# según la función que el LLM haya invocado.
SCHEMA_MAP: dict[str, tuple[str, dict]] = {
    "buscar_ofertas_empleo": ("respuesta_busqueda_empleo", SCHEMA_OFERTAS),
    "generar_carta_presentacion": ("carta_de_presentacion", SCHEMA_CARTA),
    "extraer_datos_cv": ("datos_cv_estructurados", SCHEMA_DATOS_CV),
}
