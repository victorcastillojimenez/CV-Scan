"""
Módulo principal de la Agencia de Colocación Inteligente.

Define la clase `AgenciaColocacion` que orquesta 4 agentes especializados
en un flujo secuencial para analizar CVs, buscar empleos, investigar
empresas y redactar postulaciones personalizadas.

Se aplica un monkey-patch sobre `litellm.completion` para interceptar
los errores 429 (rate-limit) a nivel más bajo que CrewAI, forzando
esperas automáticas con backoff antes de reintentar.
"""

import os
import re
import time
from pathlib import Path
from typing import Any

import litellm
from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

from core.exceptions import AgencyConfigError

# ── Directorio base del proyecto ─────────────────────────
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# ── Constantes ───────────────────────────────────────────
DEFAULT_MODEL: str = "groq/llama-3.1-8b-instant"
DEFAULT_TEMPERATURE: float = 0.4
AGENT_MAX_RPM: int = 2
AGENT_MAX_ITER: int = 5

# Segundos mínimos de espera antes de reintentar tras un 429
BASE_WAIT_SECONDS: float = 20.0
MAX_RETRIES: int = 12


# ═══════════════════════════════════════════════════════════
# MONKEY-PATCH: Reintento con espera a nivel de litellm
# ═══════════════════════════════════════════════════════════
# CrewAI captura el RateLimitError antes de que litellm pueda
# reintentar. Este parche intercepta la llamada a nivel más
# bajo para que las esperas se ejecuten DENTRO de la función
# de completion, transparentes para CrewAI.

_original_completion = litellm.completion


def _extract_retry_delay(error_message: str) -> float:
    """Extrae el delay sugerido por Groq del mensaje de error.

    Args:
        error_message: Texto del error que contiene 'try again in Xs'.

    Returns:
        Segundos de espera extraídos, o BASE_WAIT_SECONDS si no se encuentra.
    """
    match = re.search(r"try again in (\d+\.?\d*)s", error_message)
    if match:
        return float(match.group(1)) + 2.0  # Margen de seguridad de 2s
    return BASE_WAIT_SECONDS


def _completion_with_retry(*args: Any, **kwargs: Any) -> Any:
    """Wrapper sobre litellm.completion con reintentos automáticos.

    Captura errores 429 (RateLimitError) y duerme el tiempo que
    indica Groq antes de reintentar, hasta MAX_RETRIES veces.

    Raises:
        El error original si se agotan todos los reintentos.
    """
    for attempt in range(MAX_RETRIES):
        try:
            return _original_completion(*args, **kwargs)
        except litellm.RateLimitError as exc:
            if attempt >= MAX_RETRIES - 1:
                raise

            wait = _extract_retry_delay(str(exc))
            print(
                f"  ⏳ Rate-limit alcanzado (intento {attempt + 1}/{MAX_RETRIES}). "
                f"Esperando {wait:.0f}s antes de reintentar..."
            )
            time.sleep(wait)
        except litellm.APIConnectionError:
            # Reconexión tras timeout de red
            if attempt >= MAX_RETRIES - 1:
                raise
            time.sleep(5.0)


# Aplicar el monkey-patch globalmente
litellm.completion = _completion_with_retry
litellm.drop_params = True


# ═══════════════════════════════════════════════════════════
# CLASE PRINCIPAL
# ═══════════════════════════════════════════════════════════

@CrewBase
class AgenciaColocacion:
    """Agencia de Colocación Inteligente basada en CrewAI.

    Orquesta un flujo **secuencial** de 4 agentes especializados:
        1. career_profiler  → Analiza el CV y propone roles.
        2. job_market_scout → Busca ofertas reales en internet.
        3. corporate_culture_researcher → Investiga las empresas.
        4. application_strategist → Redacta mensajes de postulación.

    El monkey-patch sobre litellm.completion garantiza que los
    errores 429 se resuelven con esperas automáticas en vez de
    explotar la ejecución.

    Raises:
        AgencyConfigError: Si falta la GROQ_API_KEY en el entorno.
    """

    agents_config: str = str(BASE_DIR / "config" / "agents.yaml")
    tasks_config: str = str(BASE_DIR / "config" / "tasks.yaml")

    def __init__(self) -> None:
        """Inicializa el LLM y las herramientas compartidas.

        Raises:
            AgencyConfigError: Si GROQ_API_KEY no está definida.
        """
        groq_api_key: str | None = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise AgencyConfigError(
                "No se encontró GROQ_API_KEY en las variables de entorno."
            )

        self.llm: LLM = LLM(
            model=DEFAULT_MODEL,
            temperature=DEFAULT_TEMPERATURE,
            api_key=groq_api_key,
        )

        self.search_tool: SerperDevTool = SerperDevTool()

    # ==========================================
    # AGENTES
    # ==========================================

    @agent
    def career_profiler(self) -> Agent:
        """Agente estratega de carrera: analiza el CV e identifica roles potenciales."""
        return Agent(
            config=self.agents_config["career_profiler"],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_rpm=AGENT_MAX_RPM,
            max_iter=AGENT_MAX_ITER,
        )

    @agent
    def job_market_scout(self) -> Agent:
        """Agente cazador de empleos: busca ofertas reales con herramientas de búsqueda."""
        return Agent(
            config=self.agents_config["job_market_scout"],
            tools=[self.search_tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_rpm=AGENT_MAX_RPM,
            max_iter=AGENT_MAX_ITER,
        )

    @agent
    def corporate_culture_researcher(self) -> Agent:
        """Agente investigador corporativo: estudia la cultura y valores de las empresas."""
        return Agent(
            config=self.agents_config["corporate_culture_researcher"],
            tools=[self.search_tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_rpm=AGENT_MAX_RPM,
            max_iter=AGENT_MAX_ITER,
        )

    @agent
    def application_strategist(self) -> Agent:
        """Agente redactor: crea mensajes de postulación personalizados."""
        return Agent(
            config=self.agents_config["application_strategist"],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_rpm=AGENT_MAX_RPM,
            max_iter=AGENT_MAX_ITER,
        )

    # ==========================================
    # TAREAS
    # ==========================================

    @task
    def profile_assessment_task(self) -> Task:
        """Tarea de análisis de perfil: extrae habilidades y sugiere roles."""
        return Task(
            config=self.tasks_config["profile_assessment_task"],
            agent=self.career_profiler(),
        )

    @task
    def job_scouting_task(self) -> Task:
        """Tarea de búsqueda: localiza ofertas reales que encajen con el perfil."""
        return Task(
            config=self.tasks_config["job_scouting_task"],
            agent=self.job_market_scout(),
        )

    @task
    def company_intelligence_task(self) -> Task:
        """Tarea de inteligencia empresarial: investiga las empresas candidatas."""
        return Task(
            config=self.tasks_config["company_intelligence_task"],
            agent=self.corporate_culture_researcher(),
        )

    @task
    def custom_outreach_drafting_task(self) -> Task:
        """Tarea de redacción: genera mensajes de postulación personalizados."""
        return Task(
            config=self.tasks_config["custom_outreach_drafting_task"],
            agent=self.application_strategist(),
            output_file="reporte_postulacion.md",
        )

    # ==========================================
    # CREW
    # ==========================================

    @crew
    def crew(self) -> Crew:
        """Crea la Agencia con flujo SECUENCIAL y reintentos a nivel de litellm.

        Returns:
            Crew: Instancia configurada y lista para ejecutarse.
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=False,
            verbose=True,
        )
