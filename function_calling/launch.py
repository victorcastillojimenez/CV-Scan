"""
Punto de entrada para probar las 3 Function Callings de CV SCAN AI.

Ejecuta 3 casos de prueba que ejercitan cada función:
  1. Extracción de datos estructurados del CV
  2. Búsqueda de ofertas de empleo
  3. Generación de carta de presentación

Uso:
    python -m function_calling.launch <ruta_cv.pdf>

Ejemplo:
    python -m function_calling.launch mi_cv.pdf
"""

import json
import logging
import sys

from dotenv import load_dotenv

from function_calling.manage_cv import gestionar_cv

# ── Configuración ──────────────────────────────────────────────
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# ── Mensajes de prueba ─────────────────────────────────────────
MENSAJES_TEST: list[str] = [
    "Extrae los datos estructurados de mi CV",
    "Busca ofertas de trabajo de Data Analyst en Madrid en remoto",
    (
        "Genera una carta de presentación para la empresa Google, "
        "puesto Software Engineer, tono formal"
    ),
]


def main() -> None:
    """Ejecuta los 3 casos de prueba de Function Calling."""
    if len(sys.argv) < 2:
        print("Uso: python -m function_calling.launch <ruta_cv.pdf>")
        print("Ejemplo: python -m function_calling.launch mi_cv.pdf")
        sys.exit(1)

    cv_path = sys.argv[1]
    print(f"\n📄 CV: {cv_path}")

    for i, mensaje in enumerate(MENSAJES_TEST, 1):
        print(f"\n{'=' * 60}")
        print(f"  🧪 Test #{i}")
        print(f"  📩 Mensaje: {mensaje}")
        print(f"{'=' * 60}\n")

        try:
            resultado = gestionar_cv(mensaje, cv_path)
            print(json.dumps(resultado, indent=2, ensure_ascii=False))
        except Exception as exc:
            print(f"❌ Error: {exc}")

        print(f"\n{'-' * 60}")

    print("\n✅ Todos los tests completados.\n")


if __name__ == "__main__":
    main()
