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
                    "titulo": {"type": "string"},
                    "empresa": {"type": "string"},
                    "ubicacion": {"type": "string"},
                    "url": {"type": "string"},
                    "descripcion_breve": {"type": "string"},
                    "relevancia": {
                        "type": "string",
                        "enum": ["alta", "media", "baja"],
                    },
                },
                "required": [
                    "titulo",
                    "empresa",
                    "ubicacion",
                    "url",
                    "descripcion_breve",
                    "relevancia",
                ],
                "additionalProperties": False,
            },
        },
        "resumen": {
            "type": "string",
            "description": (
                "Resumen general del mercado laboral para el perfil buscado"
            ),
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
            "description": "Línea de asunto del email de presentación",
        },
        "saludo": {"type": "string"},
        "cuerpo": {
            "type": "string",
            "description": "Cuerpo principal de la carta de presentación",
        },
        "despedida": {"type": "string"},
        "tono_detectado": {
            "type": "string",
            "enum": ["formal", "semiformal", "creativo"],
        },
    },
    "required": ["asunto", "saludo", "cuerpo", "despedida", "tono_detectado"],
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
