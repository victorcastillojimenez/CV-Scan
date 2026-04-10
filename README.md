# 🚀 CV SCAN AI — Agencia de Colocación Inteligente

Aplicación web Streamlit que combina **análisis de CV con IA**, un sistema **multi-agente CrewAI** y **RAG (Retrieval Augmented Generation)** para un asesoramiento basado en conocimiento experto.

## Funcionalidades

| Pestaña | Descripción |
|---------|-------------|
| 📊 **Reporte Ejecutivo** | Análisis del CV enriquecido con RAG (nota, fortalezas, mejoras, roles) |
| 🤖 **Agencia CrewAI** | Pipeline de 4 agentes que buscan ofertas reales y redactan postulaciones |
| 💬 **Chat Asistente** | Chatbot con RAG dinámico sobre el CV y mejores prácticas de RRHH |

## Arquitectura del Sistema

### 1. Multi-Agente CrewAI
El sistema usa **4 agentes especializados** en un flujo **jerárquico** supervisado por un Manager LLM:

```
👔 Manager LLM (coordinador)
 ├── 🎯 career_profiler      → Analiza CV y sugiere roles     [FileReadTool]
 ├── 🔍 job_market_scout     → Busca ofertas reales online    [SerperDevTool]
 ├── 🏢 culture_researcher   → Investiga cultura empresarial  [SerperDevTool]
 └── ✍️ app_strategist       → Redacta postulaciones
```

### 2. Sistema RAG (Retrieval Augmented Generation)
Para garantizar que el análisis y el chat sigan estándares profesionales, se implementó un sistema RAG:

- **Motor Vectorial**: [ChromaDB](https://www.trychroma.com/) (persistente en disco).
- **Embeddings**: `all-MiniLM-L6-v2` vía [SentenceTransformers](https://www.sbert.net/).
- **Base de Conocimiento**: PDFs expertos situados en `/conocimiento_cv`.
- **Integración**: Los agentes y el chat consultan automáticamente esta base para fundamentar sus críticas y consejos.

## Requisitos

- Python 3.11+
- API Key de [Groq](https://console.groq.com/) (LLM rápido)
- API Key de [Serper](https://serper.dev/) (búsquedas web)
- (Opcional) [Ollama](https://ollama.com/) para ejecución local.

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
```

## Configuración

1. Crear un archivo `.env` en la raíz basado en `.env.example`:
```env
GROQ_API_KEY=tu_clave_groq_aqui
SERPER_API_KEY=tu_clave_serper_aqui
```
2. (Opcional) Añade tus propios PDFs de expertos en la carpeta `conocimiento_cv/` para que el RAG los aprenda.

## Uso

```bash
streamlit run main.py
```

1. Sube un CV en formato PDF.
2. Usa **⚡ Analizar Perfil** para obtener el reporte (usa RAG para comparar tu CV con estándares).
3. Usa **🚀 Lanzar Agencia** para activar los agentes CrewAI.
4. Chatea con el asistente; responderá usando tanto tu CV como la base de conocimiento RAG.

## Estructura del proyecto

```
crew_AI/
├── .streamlit/config.toml     # Tema dark neon
├── assets/                    # Logos y banners
├── config/
│   ├── agents.yaml            # Configuración de agentes
│   └── tasks.yaml             # Definición de tareas
├── conocimiento_cv/           # [NUEVO] PDFs para el sistema RAG
├── core/
│   ├── agencia_crew.py        # Clase principal CrewAI
│   ├── rag.py                 # [NUEVO] Lógica de ChromaDB y embeddings
│   ├── styles.py              # CSS neon dark theme
│   └── utils.py               # Extracción PDF y cliente LLM
├── db_cv_expert/              # [NUEVO] Base de datos vectorial persistente
├── main.py                    # App Streamlit (punto de entrada)
├── requirements.txt           # Dependencias (incluye chromadb, torch)
└── .env                       # Variables de entorno
```

## Tests

```bash
python -m pytest tests/ -v
```

## Licencia

Proyecto académico — uso educativo.

