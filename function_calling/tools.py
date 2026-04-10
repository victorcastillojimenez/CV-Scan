"""
Definiciones de herramientas (tools) para Function Calling.

Cada herramienta describe una función que el LLM puede invocar
cuando lo considere necesario según la petición del usuario.
Formato compatible con la API Responses de OpenAI.
"""

TOOLS: list[dict] = [
    {
        "type": "function",
        "name": "buscar_ofertas_empleo",
        "description": (
            "Busca ofertas de empleo reales en internet según el rol, "
            "ubicación y modalidad indicados. Devuelve resultados "
            "actualizados del mercado laboral."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "rol": {
                    "type": "string",
                    "description": "Puesto o rol profesional a buscar (ej: Data Analyst)",
                },
                "ubicacion": {
                    "type": "string",
                    "description": "Ciudad o zona geográfica (ej: Madrid, Barcelona, remoto)",
                },
                "modalidad": {
                    "type": "string",
                    "description": "Tipo de modalidad laboral",
                    "enum": ["presencial", "remoto", "hibrido"],
                },
            },
            "required": ["rol", "ubicacion", "modalidad"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "generar_carta_presentacion",
        "description": (
            "Prepara el contexto necesario para generar una carta de "
            "presentación profesional. Lee el CV del candidato y consulta "
            "la base de conocimiento experto sobre buenas prácticas."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "empresa": {
                    "type": "string",
                    "description": "Nombre de la empresa destino",
                },
                "puesto": {
                    "type": "string",
                    "description": "Puesto al que se postula",
                },
                "tono": {
                    "type": "string",
                    "description": "Tono deseado para la carta",
                    "enum": ["formal", "semiformal", "creativo"],
                },
            },
            "required": ["empresa", "puesto", "tono"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "extraer_datos_cv",
        "description": (
            "Lee un archivo PDF de CV y extrae su contenido como texto "
            "plano para su posterior análisis estructurado."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ruta_cv": {
                    "type": "string",
                    "description": "Ruta al archivo PDF del CV",
                },
            },
            "required": ["ruta_cv"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]
