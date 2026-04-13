"""
Extractor de datos estructurados del CV.

Lee un PDF del CV y extrae información clave de forma estructurada:
- Datos personales (nombre, email, teléfono, ubicación)
- Habilidades técnicas
- Experiencia profesional
- Educación

Esta información se reutiliza en las function calls para personalizar
cartas de presentación, búsquedas de empleo, etc.
"""

import json
import logging
from typing import Optional

from openai import OpenAI

logger = logging.getLogger(__name__)


class ExtractorCV:
    """Extrae datos estructurados de un CV usando GPT."""

    def __init__(self, api_key: Optional[str] = None):
        """Inicializa el extractor con un cliente OpenAI."""
        import os
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
        self._cache = {}

    def extraer_datos_estructurados(self, texto_cv: str) -> dict:
        """
        Extrae datos estructurados del CV usando GPT.

        Args:
            texto_cv: Texto completo del CV extractado del PDF

        Returns:
            Diccionario con datos estructurados del CV
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "user",
                        "content": f"""Extrae los siguientes datos del CV y devuelve un JSON válido.
Retorna SOLO un JSON válido sin markdown.

CV:
{texto_cv}

Estructura esperada:
{{
    "nombre": "Nombre completo del candidato",
    "email": "email@ejemplo.com",
    "telefono": "+34 XXX XXX XXX",
    "ubicacion": "Ciudad, País",
    "titulo_profesional": "Cargo/Título principal",
    "resumen": "Resumen breve (1-2 líneas) del perfil profesional",
    "habilidades": ["Habilidad 1", "Habilidad 2"],
    "lenguajes_programacion": ["Python", "Java"],
    "tecnologias": ["SQL", "MongoDB"],
    "experiencia_anos": 3,
    "educacion": [{{"titulo": "Grado/Máster", "institucion": "Universidad", "ano": 2020}}],
    "idiomas": {{"español": "nativo", "ingles": "intermedio"}},
    "proyectos_destacados": ["Proyecto 1", "Proyecto 2"]
}}

Si algún campo no está disponible, usa null.""",
                    }
                ],
            )

            datos = {}
            try:
                content = response.choices[0].message.content
                datos = json.loads(content)
                logger.info(f"✓ Datos extraídos del CV para {datos.get('nombre', 'Desconocido')}")
            except json.JSONDecodeError as e:
                logger.error(f"⚠️  No se pudo parsear JSON: {e}")
                
            return datos or {}
        except Exception as e:
            logger.error(f"❌ Error extrayendo datos del CV: {e}")
            return {}

    def obtener_contexto_cv(self, texto_cv: str) -> str:
        """
        Genera un contexto textual del CV para usar en prompts.

        Útil para pasar al LLM información sobre el candidato sin
        deber extraer datos estructurados.

        Args:
            texto_cv: Texto completo del CV

        Returns:
            String formateado con contexto del CV
        """
        datos = self.extraer_datos_estructurados(texto_cv)

        if not datos:
            return ""

        contexto = f"""
PERFIL DEL CANDIDATO:
─────────────────────
Nombre: {datos.get('nombre', 'N/A')}
Email: {datos.get('email', 'N/A')}
Teléfono: {datos.get('telefono', 'N/A')}
Ubicación: {datos.get('ubicacion', 'N/A')}
Perfil: {datos.get('titulo_profesional', 'N/A')}
Experiencia: {datos.get('experiencia_anos', '?')} años

RESUMEN:
{datos.get('resumen', 'N/A')}

HABILIDADES TÉCNICAS:
{', '.join(datos.get('lenguajes_programacion', [])) if datos.get('lenguajes_programacion') else 'N/A'}

TECNOLOGÍAS:
{', '.join(datos.get('tecnologias', [])) if datos.get('tecnologias') else 'N/A'}

IDIOMAS:
{', '.join([f"{idioma}: {nivel}" for idioma, nivel in (datos.get('idiomas') or {}).items()]) if datos.get('idiomas') else 'N/A'}
"""
        return contexto.strip()


def extraer_datos_cv(ruta_pdf: str) -> dict:
    """
    Función pública para extraer datos del CV.

    Args:
        ruta_pdf: Ruta al archivo PDF del CV

    Returns:
        Diccionario con datos estructurados
    """
    from function_calling.my_functions import _leer_pdf

    try:
        texto_cv = _leer_pdf(ruta_pdf)
        extractor = ExtractorCV()
        datos = extractor.extraer_datos_estructurados(texto_cv)
        return datos or {}
    except Exception as e:
        logger.error(f"Error extrayendo datos del CV: {e}")
        return {}
