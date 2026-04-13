# 🚀 CV SCAN AI — Agencia de Colocación Inteligente

Aplicación web **Streamlit** que combina **análisis de CV con IA**, un sistema **multi-agente CrewAI**, **RAG (Retrieval Augmented Generation)** y **Function Calling** avanzado para asesoramiento profesional basado en conocimiento experto.

## ✨ Características Principales

| Pestaña | Descripción |
|---------|-------------|
| 📊 **Reporte Ejecutivo** | Análisis del CV enriquecido con RAG (nota, fortalezas, mejoras, roles) |
| 🤖 **Agencia CrewAI** | Pipeline de 4 agentes que buscan ofertas reales y redactan postulaciones |
| 💬 **Chat Asistente** | Chatbot con RAG dinámico sobre el CV y mejores prácticas de RRHH |
| 🔧 **Function Calling Inteligente** | 3 funciones autoejecutables con fallbacks automáticos cuando fallan APIs |

---

## 🧠 Arquitectura del Sistema

### 1. Sistema de Function Calling (OpenAI + Fallbacks)

La aplicación implementa un sistema de **function calling inteligente** que permite al LLM invocar funciones Específicas de forma automática:

#### **3 Funciones Principales:**

```python
┌─────────────────────────────────────────────────────────────┐
│                   FUNCTION CALLING (OpenAI)                 │
├─────────────────────────────────────────────────────────────┤

1️⃣  buscar_ofertas_empleo(rol, ubicacion, modalidad)
    ├─ Intenta: API Serper → Búsqueda web real
    └─ Fallback: Ofertas hardcodeadas personalizadas para Victor
       • Backend Engineer (FastAPI) - DataFlow AI
       • ML Engineer / Data Scientist - BigData Insights
       • Full Stack Developer - Desarrollo Web Integral
       • DevOps Engineer - CloudTech
       • AI/LLM Developer - NeuroAI Innovación

2️⃣  generar_carta_presentacion(empresa, puesto, tono, cv_path)
    ├─ Intenta: OpenAI GPT + RAG → Carta personalizada dinámica
    └─ Fallback: Carta profesional hardcodeada para NeuroAI
       • Asunto: "Solicitud: Posición de AI/LLM Developer en NeuroAI"
       • Cuerpo: 4 párrafos completos y listos para enviar
       • Firma: Datos de contacto personalizados

3️⃣  extraer_datos_cv(ruta_cv)
    ├─ Intenta: OpenAI GPT → Extrae datos de cualquier CV
    └─ Fallback: Datos JSON hardcodeados de Victor Castillo
       • Datos personales, habilidades, experiencia
       • Lenguajes: Python, Java, C#, JavaScript, R
       • Tecnologías: FastAPI, Angular, Docker, etc.
       • Proyectos: TFG Lesiones Deportivas, Agente NLP

└─────────────────────────────────────────────────────────────┘
```

#### **Flujo de Fallback Automático:**

```
┌─ Usuario pide: "Buscame trabajo" ──┐
│                                      │
├─ ¿Existe OpenAI API Key válida?     │
│   ├─ SÍ: Usa function calling de OpenAI (máxima calidad) ✅
│   │    └─ OpenAI invoca buscar_ofertas_empleo()
│   │       └─ Serper busca ofertas reales en internet
│   │
│   └─ NO / FALLA (401, etc): Fallback automático 🔄
│        └─ Detecta tipo: "buscar" = buscar_ofertas_empleo()
│           └─ Ejecuta función con datos hardcodeados
│              └─ Envía JSON a Groq para formatear bonito ✨
│
├─ LLM Groq formatea con emojis, títulos, estructura
└─ Usuario ve resultado profesional y legible 🎨
```

### 2. Multi-Agente CrewAI
Sistema de **4 agentes especializados** en flujo **jerárquico** supervisado por Manager LLM:

```
👔 Manager LLM (coordinador)
 ├── 🎯 career_profiler      → Analiza CV y sugiere roles     [FileReadTool]
 ├── 🔍 job_market_scout     → Busca ofertas reales online    [SerperDevTool]
 ├── 🏢 culture_researcher   → Investiga cultura empresarial  [SerperDevTool]
 └── ✍️ app_strategist       → Redacta postulaciones
```

### 3. Sistema RAG (Retrieval Augmented Generation)
Sistema de **base de conocimiento inteligente** con ChromaDB para enriquecer respuestas:

- **Motor Vectorial**: [ChromaDB](https://www.trychroma.com/) (persistente en disco)
- **Embeddings**: `all-MiniLM-L6-v2` vía [SentenceTransformers](https://www.sbert.net/)
- **Base de Conocimiento**: PDFs expertos en `/conocimiento_cv`
- **Integración**: Agentes y chat consultan automáticamente la base

---

## 📋 Archivos Clave

```
function_calling/
├── my_functions.py              ⭐ FUNCIONES PRINCIPALES
│   ├─ buscar_ofertas_empleo()           (con fallback de 5 ofertas)
│   ├─ generar_carta_presentacion()      (con fallback de carta)
│   ├─ extraer_datos_cv()                (con fallback de datos)
│   └─ _extraer_datos_cv_fallback()      (datos hardcodeados Victor)
│
├── cv_extractor.py              🔍 EXTRACTOR CON OpenAI
│   ├─ ExtractorCV.extraer_datos_estructurados()  (dinámico con IA)
│   └─ ExtractorCV.obtener_contexto_cv()
│
├── manage_cv.py                 🔧 ORQUESTADOR function calling
│   └─ gestionar_cv()            (OpenAI + tools + schemas)
│
├── tools.py                     🛠️ DEFINICIÓN DE HERRAMIENTAS
│   └─ TOOLS                     (descripción de 3 funciones)
│
└── schemas.py                   📐 ESQUEMAS JSON
    ├─ SCHEMA_OFERTAS            (estructura respuesta ofertas)
    ├─ SCHEMA_CARTA              (estructura respuesta carta)
    └─ SCHEMA_MAP                (mapeo función → schema)

core/
├── agencia_crew.py              🤖 AGENTIA MULTRIAGENTE
├── rag.py                       🧠 SISTEMA RAG + ChromaDB
├── styles.py                    🎨 ESTILOS STREAMLIT
└── utils.py                     ⚙️ UTILIDADES

main.py                          🚀 APLICACIÓN STREAMLIT (punto entrada)
```

---

## 🚀 Requisitos y Configuración

### Dependencias
- Python 3.11+
- [Groq API Key](https://console.groq.com/) (LLM rápido, gratuito)
- [Serper API Key](https://serper.dev/) (búsquedas web)
- OpenAI API Key (OPCIONAL - para máxima calidad de function calling)

### Variables de Entorno (.env)
```env
# ✅ REQUERIDOS
GROQ_API_KEY=gsk_tu_clave_groq_aqui

# ⭐ RECOMENDADO (para búsquedas web reales)
SERPER_API_KEY=tu_clave_serper_aqui

# 🔧 OPCIONAL (si falla, usa fallbacks automáticos)
OPENAI_API_KEY=sk-tu_clave_openai_aqui

# ⚙️ CONFIGURACIÓN
ANONYMIZED_TELEMETRY=False
OTEL_SDK_DISABLED=true
```

### Instalación

```bash
# 1. Clonar repositorio
git clone <url-del-repo>
cd crew_AI

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear archivo .env con API keys
cp .env.example .env  # Rellenar con tus claves
```

---

## 💻 Uso

```bash
streamlit run main.py
```

### Flujo de Usuario:

1. **📤 Subir CV** → Carga PDF de tu currículum
2. **📊 Reporte Pestaña**:
   - Click en "⚡ Analizar Perfil"
   - RAG enriquece análisis con mejores prácticas
   - Obtén nota, fortalezas, mejoras, roles recomendados
3. **🤖 Agencia Pestaña**:
   - Click en "🚀 Lanzar Agencia"
   - 4 agentes buscan ofertas y redactan postulaciones
4. **💬 Chat Pestaña**:
   - Pregunta lo que quieras sobre tu CV
   - Chatbot responde usando RAG dinámico
5. **🔧 Function Calling Automático**:
   - Escribe: "Buscame trabajo según mi perfil"
   - Sistema detecta intención → Invoca función adecuada
   - Resultado formateado y profesional

---

## ⚡ Comportamiento sin APIs

| Escenario | Comportamiento |
|-----------|----------------|
| OpenAI ✅ + Serper ✅ | Function calling OpenAI + búsquedas reales |
| OpenAI ❌ + Serper ✅ | Function calling fallback + búsquedas reales |
| OpenAI ❌ + Serper ❌ | Function calling fallback + ofertas hardcodeadas |
| Solo Groq | Chat con RAG (Agencia y Reporte funcionan) |

**La app siempre funciona** porque tiene fallbacks en cascada ✨

---

## 🎯 Ejemplos de Uso

### Ejemplo 1: Buscar Ofertas (Con Fallback)
```
👤 Usuario: "Buscame trabajo de Backend en Madrid"

🤖 Sistema:
  1. Intenta OpenAI + Serper → Búsqueda real
  2. Si falla → Ofertas fallback personalizadas
  3. Envía a Groq → Formatea bonito
  4. Resultado: 5 ofertas con descripción profesional

🎯 Resultado:
✅ Backend Engineer (FastAPI) - DataFlow AI Solutions
   Descripción, salario, modalidad, beneficios...
```

### Ejemplo 2: Generar Carta (Con Fallback)
```
👤 Usuario: "Generame una carta para NeuroAI"

🤖 Sistema:
  1. Intenta OpenAI + RAG → Carta personal dinámica
  2. Si falla → Carta fallback profesional hardcodeada
  3. Resultado: Carta lista para copiar/pegar

📧 Resultado:
Estimado equipo de selección de NeuroAI,

Me dirijo a ustedes para expresar mi interés en la posición 
de AI/LLM Developer...
[carta completa de 4 párrafos]
```

### Ejemplo 3: Extraer Datos CV (Con Fallback)
```
👤 Usuario: "Extrae mis datos del CV"

🤖 Sistema:
  1. Intenta OpenAI → Extrae dinámicamente cualquier CV
  2. Si falla → Datos JSON fallback (Victor)
  3. Resultado: JSON estructurado

📊 Resultado:
{
  "nombre": "Victor Castillo Jimenez",
  "email": "victorcastillojimenez04@gmail.com",
  "lenguajes_programacion": ["Python", "Java", "C#", ...],
  "tecnologias": ["FastAPI", "Angular", "Docker", ...],
  ...
}
```

---

## 📦 Estructura del Proyecto

```
crew_AI/
├── 📄 main.py                     # Aplicación Streamlit (entrada)
├── 📘 README.md                   # Este archivo
├── ⚙️  requirements.txt           # Dependencias Python
│
├── 🔧 function_calling/
│   ├── my_functions.py            # ⭐ 3 funciones + fallbacks
│   ├── cv_extractor.py            # Extractor OpenAI (dinámico)
│   ├── manage_cv.py               # Orquestador function calling
│   ├── tools.py                   # Definición de herramientas
│   ├── schemas.py                 # Esquemas JSON estructurados
│   ├── __init__.py
│   └── schemas.py
│
├── 🧠 core/
│   ├── agencia_crew.py            # Multi-agente CrewAI
│   ├── rag.py                     # Sistema RAG + ChromaDB
│   ├── styles.py                  # Estilos CSS Streamlit
│   ├── utils.py                   # Utilidades (PDF, LLM)
│   ├── exceptions.py              # Excepciones personalizadas
│   ├── validators.py              # Validadores
│   └── __init__.py
│
├── 📚 conocimiento_cv/            # Base de conocimiento RAG
│   └── *.pdf                      # PDFs expertos para RAG
│
├── 🗄️  db_cv_expert/              # ChromaDB persistente
│   ├── chroma.sqlite3             # Base vectorial
│   └── [ID]/                      # Embeddings
│
├── ⚙️  config/
│   ├── agents.yaml                # Config agentes
│   ├── tasks.yaml                 # Config tareas
│   └── [variables]
│
└── 🎨 assets/
    └── *.png                      # Logos e imágenes
```

---

## 🔐 API Keys Necesarias

| API | Uso | Coste | Requerida? |
|-----|-----|-------|-----------|
| **Groq** | LLM rápido (chat, agencia) | ✅ GRATIS | ✅ SÍ |
| **Serper** | Búsquedas web reales | 💰 $5/mes aprox | ⭐ Recomendado |
| **OpenAI** | Function calling de alta calidad | 💰 Variable | 🔧 Opcional |

> **Si no tienes OpenAI**: Los fallbacks mantienen la app 100% funcional

---

## 🚦 Solución de Problemas

| Problema | Solución |
|----------|----------|
| "GROQ_API_KEY no configurada" | Añade GROQ_API_KEY a .env |
| "Function calling falló 401" | Tu OpenAI key es inválida, usa fallback ✅ |
| "ChromaDB error" | Elimina carpeta `db_cv_expert/` y reinicia |
| "PDF no se lee" | Asegúrate CV es legible (no escaneado) |
| "Chat lento" | Groq tiene rate limit, espera 1-2 min |

---

## 🎓 Aprendizajes Técnicos

Este proyecto implementa:

- ✅ **Function Calling** con OpenAI + fallbacks automáticos
- ✅ **Cascading Fallbacks** (OpenAI → Fallback → Groq)
- ✅ **RAG (Retrieval Augmented Generation)** con ChromaDB
- ✅ **Multi-Agente CrewAI** (Manager + 4 especialistas)
- ✅ **Streamlit** para interfaz web reactiva
- ✅ **LLM Groq** para LLM rápido y económico
- ✅ **Serper API** para búsquedas web en tiempo real
- ✅ **PDFs** con PyPDF2
- ✅ **JSON Schemas** para respuestas estructuradas

---

## 📝 Notas Importantes

1. **Victor Castillo** es el candidato de ejemplo. Los fallbacks están personalizados para él
2. Los fallbacks funcionan sin internet (datos hardcodeados)
3. Groq formatea automáticamente JSON en respuestas bonitas
4. RAG mejora la calidad de análisis significativamente
5. Creación de agentes es lenta (15-30 seg) - es normal

---

## 🤝 Contribuciones

Para mejorar:
1. Añade más PDFs a `conocimiento_cv/`
2. Reemplaza fallbacks hardcodeados con otros candidatos
3. Mejora prompts en `config/agents.yaml`
4. Añade más esquemas de respuesta en `function_calling/schemas.py`

---

## 📄 Licencia

MIT - Libre para uso personal y comercial

---

**Desarrollado por Victor Castillo Jimenez** | Especialización en IA y Big Data | Instituto Nebrija
python -m pytest tests/ -v
```

## Licencia

Proyecto académico — uso educativo.

