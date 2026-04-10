"""
Módulo principal de la Agencia de Colocación Inteligente.

Define la clase `AgenciaColocacion` que orquesta 4 agentes especializados
en un flujo secuencial para analizar CVs, buscar empleos, investigar
empresas y redactar postulaciones personalizadas.

Se emplea el proceso SEQUENTIAL en lugar de HIERARCHICAL para evitar
que CrewAI instancie un 5.º agente "manager" invisible que multiplica
el consumo de tokens y dispara el rate-limit del tier gratuito de Groq.
"""

import os
from pathlib import Path

from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

from core.exceptions import AgencyConfigError

# Directorio base del proyecto (parent de core/)
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# ── Constantes de configuración del LLM ──────────────────
# llama-3.1-8b-instant tiene 30 000 TPM en Groq Free (vs 6 000 del 70b)
DEFAULT_MODEL: str = "groq/llama-3.1-8b-instant"
DEFAULT_TEMPERATURE: float = 0.4
MAX_RETRIES: int = 5
REQUEST_TIMEOUT: int = 120

# Máx. peticiones por minuto — impone una cadencia que respeta el rate-limit
AGENT_MAX_RPM: int = 6
# Máx. iteraciones internas por agente — evita bucles infinitos de reintento
AGENT_MAX_ITER: int = 5


@CrewBase
class AgenciaColocacion:
    """Agencia de Colocación Inteligente basada en CrewAI.

    Orquesta un flujo **secuencial** de 4 agentes especializados:
        1. career_profiler  → Analiza el CV y propone roles.
        2. job_market_scout → Busca ofertas reales en internet.
        3. corporate_culture_researcher → Investiga las empresas.
        4. application_strategist → Redacta mensajes de postulación.

    El flujo secuencial pasa la salida de cada tarea como contexto
    a la siguiente, consumiendo ~60 % menos tokens que el jerárquico.

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
            max_retries=MAX_RETRIES,
            request_timeout=REQUEST_TIMEOUT,
        )

        # SerperDevTool: búsqueda de ofertas y cultura empresarial en vivo
        self.search_tool: SerperDevTool = SerperDevTool()

    # ==========================================
    # DEFINICIÓN DE AGENTES (Decoradores @agent)
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
    # DEFINICIÓN DE TAREAS (Decoradores @task)
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
    # ENSAMBLAJE DE LA CREW
    # ==========================================

    @crew
    def crew(self) -> Crew:
        """Crea la Agencia con un flujo de trabajo SECUENCIAL.

        El flujo secuencial encadena las tareas una tras otra,
        pasando el resultado de cada una como contexto a la siguiente.
        Esto elimina el agente manager del modo jerárquico y reduce
        el consumo de tokens en ~60 %, evitando los rate-limits.

        Returns:
            Crew: Instancia configurada y lista para ejecutarse.
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            # Deshabilitado para evitar el error 401 de embeddings
            memory=False,
            verbose=True,
        )
