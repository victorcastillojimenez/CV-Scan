"""
Validación de datos de entrada para la Agencia de Colocación.
"""

from core.exceptions import InputValidationError

# Longitud mínima (en caracteres) para considerar válido un CV
MIN_CV_LENGTH: int = 50


def validate_inputs(inputs: dict[str, str]) -> None:
    """Valida que los datos de entrada contengan los campos requeridos.

    Args:
        inputs: Diccionario con los datos del estudiante.
            Debe contener 'nombre_estudiante' y 'cv_text'.

    Raises:
        InputValidationError: Si falta algún campo o el CV está vacío/corto.
    """
    nombre: str | None = inputs.get("nombre_estudiante")
    cv_text: str | None = inputs.get("cv_text")

    if not nombre or not nombre.strip():
        raise InputValidationError(
            "El campo 'nombre_estudiante' es obligatorio."
        )

    if not cv_text or len(cv_text.strip()) < MIN_CV_LENGTH:
        raise InputValidationError(
            f"El campo 'cv_text' debe tener al menos {MIN_CV_LENGTH} "
            f"caracteres. Se recibieron {len(cv_text.strip()) if cv_text else 0}."
        )
