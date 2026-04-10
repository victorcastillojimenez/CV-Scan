"""
Excepciones personalizadas para la Agencia de Colocación Inteligente.

Cada excepción cubre un dominio de error específico, facilitando
el diagnóstico y la recuperación granular de fallos.
"""


class AgencyBaseError(Exception):
    """Excepción base para todos los errores de la agencia."""


class AgencyConfigError(AgencyBaseError):
    """Error de configuración: variables de entorno, YAML mal formado, etc."""


class LLMConnectionError(AgencyBaseError):
    """Error de conexión o autenticación con el proveedor de LLM (Groq)."""


class InputValidationError(AgencyBaseError):
    """Error de validación de datos de entrada (CV vacío, campos faltantes)."""


class CrewExecutionError(AgencyBaseError):
    """Error durante la ejecución del crew (fallos de agentes o tareas)."""
