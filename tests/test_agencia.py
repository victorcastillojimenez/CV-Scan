"""
Tests unitarios para la Agencia de Colocación Inteligente.

Se centran en validación de inputs y verificación de configuración,
sin depender de llamadas reales a APIs externas.
"""

import os
from unittest.mock import patch

import pytest

from core.exceptions import (
    AgencyConfigError,
    CrewExecutionError,
    InputValidationError,
)
from core.validators import validate_inputs


# =============================================
# Tests de validación de inputs
# =============================================


class TestValidateInputs:
    """Verifica que `validate_inputs` rechaza datos incompletos o inválidos."""

    def test_inputs_validos_no_lanza_excepcion(self) -> None:
        """Un input correcto no debe lanzar ninguna excepción."""
        datos: dict[str, str] = {
            "nombre_estudiante": "Ana García",
            "cv_text": "A" * 60,  # Supera el mínimo de 50 caracteres
        }
        # No debe lanzar excepción
        validate_inputs(datos)

    def test_nombre_vacio_lanza_error(self) -> None:
        """Un nombre vacío debe lanzar InputValidationError."""
        datos: dict[str, str] = {
            "nombre_estudiante": "",
            "cv_text": "A" * 60,
        }
        with pytest.raises(InputValidationError, match="nombre_estudiante"):
            validate_inputs(datos)

    def test_nombre_ausente_lanza_error(self) -> None:
        """La ausencia del campo nombre debe lanzar InputValidationError."""
        datos: dict[str, str] = {
            "cv_text": "A" * 60,
        }
        with pytest.raises(InputValidationError, match="nombre_estudiante"):
            validate_inputs(datos)

    def test_cv_vacio_lanza_error(self) -> None:
        """Un CV vacío debe lanzar InputValidationError."""
        datos: dict[str, str] = {
            "nombre_estudiante": "Ana García",
            "cv_text": "",
        }
        with pytest.raises(InputValidationError, match="cv_text"):
            validate_inputs(datos)

    def test_cv_demasiado_corto_lanza_error(self) -> None:
        """Un CV con menos de 50 caracteres debe lanzar InputValidationError."""
        datos: dict[str, str] = {
            "nombre_estudiante": "Ana García",
            "cv_text": "CV corto",
        }
        with pytest.raises(InputValidationError, match="cv_text"):
            validate_inputs(datos)

    def test_cv_solo_espacios_lanza_error(self) -> None:
        """Un CV con solo espacios en blanco debe lanzar InputValidationError."""
        datos: dict[str, str] = {
            "nombre_estudiante": "Ana García",
            "cv_text": "   " * 30,
        }
        with pytest.raises(InputValidationError, match="cv_text"):
            validate_inputs(datos)


# =============================================
# Tests de la jerarquía de excepciones
# =============================================


class TestExceptionHierarchy:
    """Verifica que la jerarquía de excepciones es coherente."""

    def test_config_error_hereda_de_base(self) -> None:
        """AgencyConfigError debe ser subtipo de AgencyBaseError."""
        with pytest.raises(AgencyConfigError):
            raise AgencyConfigError("test")

    def test_input_validation_error_hereda_de_base(self) -> None:
        """InputValidationError debe ser subtipo de AgencyBaseError."""
        with pytest.raises(InputValidationError):
            raise InputValidationError("test")

    def test_crew_execution_error_hereda_de_base(self) -> None:
        """CrewExecutionError debe ser subtipo de AgencyBaseError."""
        with pytest.raises(CrewExecutionError):
            raise CrewExecutionError("test")


# =============================================
# Tests de configuración de AgenciaColocacion
# =============================================


class TestAgenciaColocacionConfig:
    """Verifica que la AgenciaColocacion valida su configuración."""

    def test_sin_groq_key_lanza_config_error(self) -> None:
        """Sin GROQ_API_KEY debe lanzar AgencyConfigError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AgencyConfigError, match="GROQ_API_KEY"):
                from core.agencia_crew import AgenciaColocacion
                AgenciaColocacion()
