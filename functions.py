from typing import Dict, Any


def extract_cv(cv_text: str) -> Dict[str, Any]:
    """
    Función base del sistema.
    En producción, esto NO “calcula” nada.
    El LLM devuelve directamente el JSON estructurado.
    """

    # Este return es solo fallback / estructura base
    return {
        "candidato": {
            "nombre": None,
            "email": None,
            "telefono": None
        },
        "analisis_tecnico": {
            "seniority": None,
            "tecnologias_principales": [],
            "idiomas": []
        }
    }