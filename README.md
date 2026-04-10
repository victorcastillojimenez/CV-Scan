# 🚀 CV SCAN AI — Agencia de Colocación Inteligente

Aplicación web Streamlit que combina **análisis de CV con IA** y un sistema **multi-agente CrewAI** para búsqueda de empleo automatizada.

## Funcionalidades

| Pestaña | Descripción |
|---------|-------------|
| 📊 **Reporte Ejecutivo** | Análisis rápido del CV con streaming (nota, fortalezas, mejoras, roles) |
| 🤖 **Agencia CrewAI** | Pipeline de 4 agentes que buscan ofertas reales y redactan postulaciones |
| 💬 **Chat Asistente** | Chatbot contextual sobre el CV del candidato |

## Arquitectura

El sistema usa **4 agentes especializados** en un flujo **jerárquico** supervisado por un Manager LLM:

```
👔 Manager LLM (coordinador)
 ├── 🎯 career_profiler      → Analiza CV y sugiere roles     [FileReadTool]
 ├── 🔍 job_market_scout     → Busca ofertas reales online    [SerperDevTool]
 ├── 🏢 culture_researcher   → Investiga cultura empresarial  [SerperDevTool]
 └── ✍️ app_strategist       → Redacta postulaciones
```

## Requisitos

- Python 3.11+
- API Key de [Groq](https://console.groq.com/) (LLM)
- API Key de [Serper](https://serper.dev/) (búsquedas web)

## Instalación

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd crew_AI

# 2. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys
```

## Configuración

Crear un archivo `.env` en la raíz del proyecto:

```env
GROQ_API_KEY=tu_clave_groq_aqui
SERPER_API_KEY=tu_clave_serper_aqui
```

## Uso

```bash
streamlit run main.py
```

1. Sube un CV en formato PDF
2. Usa **⚡ Analizar Perfil** para obtener el reporte ejecutivo
3. Usa **🚀 Lanzar Agencia** para activar los 4 agentes CrewAI
4. Chatea con el asistente sobre el CV del candidato

## Estructura del proyecto

```
crew_AI/
├── .streamlit/config.toml   # Tema dark neon
├── assets/                  # Logos y banners
├── config/
│   ├── agents.yaml          # Configuración de agentes (roles, backstories)
│   └── tasks.yaml           # Definición de tareas (descripciones, outputs)
├── core/
│   ├── __init__.py
│   ├── agencia_crew.py      # Clase principal CrewAI (4 agentes)
│   ├── exceptions.py        # Excepciones personalizadas
│   ├── styles.py            # CSS neon dark theme
│   ├── utils.py             # Extracción PDF, conexión Groq/Ollama
│   └── validators.py        # Validación de inputs
├── tests/
│   └── test_agencia.py      # Tests unitarios
├── main.py                  # App Streamlit (punto de entrada)
├── requirements.txt         # Dependencias
└── .env                     # Variables de entorno (NO compartir)
```

## Tests

```bash
python -m pytest tests/ -v
```

## Licencia

Proyecto académico — uso educativo.
