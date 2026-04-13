"""
CV SCAN AI — Agencia de Colocación Inteligente.

Aplicación Streamlit que combina análisis de CV con un sistema
multi-agente CrewAI para búsqueda de empleo automatizada.
Incluye RAG (Retrieval Augmented Generation) para enriquecer
el análisis de CVs con conocimiento experto sobre buenas prácticas.
"""

import os
import logging
import json
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from core import styles, utils
from core.rag import consultar_rag, inicializar_coleccion, ingestar_conocimiento
from function_calling.cv_extractor import ExtractorCV

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Configuración ───────────────────────────────────────────
load_dotenv()

# Silenciar las molestas advertencias de Telemetría (SIGTERM)
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["OTEL_SDK_DISABLED"] = "true"

try:
    styles.configurar_pagina()
except Exception as exc:
    logger.warning("Error configurando página personalizada: %s", exc)
    st.set_page_config(layout="wide", page_title="CV SCAN AI")

styles.cargar_css()

# ─── Inicialización RAG ─────────────────────────────────────
# @st.cache_resource evita reinicializar ChromaDB en cada render
@st.cache_resource
def _cargar_rag():
    """Inicializa la colección RAG e ingesta los PDFs de conocimiento.
    
    Returns:
        Colección ChromaDB lista para consultas, o None si hay error.
    """
    try:
        with st.spinner("⏳ Inicializando sistema RAG..."):
            coleccion = inicializar_coleccion()
            ruta_pdfs = os.path.join(os.path.dirname(__file__), "conocimiento_cv")
            fragmentos_nuevos = ingestar_conocimiento(coleccion, ruta_pdfs)
        logger.info("RAG inicializado correctamente. Fragmentos ingestados: %d", fragmentos_nuevos)
        return coleccion
    except Exception as exc:
        logger.error("Error al inicializar RAG: %s", exc)
        st.error("⚠️ No se pudo cargar el sistema RAG. Las respuestas pueden ser menos precisas.")
        return None

coleccion_rag = _cargar_rag()

# Si el RAG no se puede cargar, las consultas devolverán cadena vacía
if coleccion_rag is None:
    logger.warning("Sistema RAG no disponible. Las consultas CAG devolverán resultados vacíos.")

# ─── Estado de sesión ────────────────────────────────────────
defaults = {
    "mensajes": [],
    "texto_pdf": "",
    "nombre_pdf": "",
    "datos_cv_extraidos": {},
    "pdf_temp_path": None,
    "analisis_realizado": "",
    "crew_resultado": "",
    "crew_running": False,
    "crew_error": "",
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo
    c1, c2, c3 = st.columns([1, 3, 1])
    with c2:
        if os.path.exists("assets/logo_icon.png"):
            st.image("assets/logo_icon.png", width=100)
        else:
            st.markdown(
                "<h2 style='text-align:center; color:#00E5FF;'>CV SCAN</h2>",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── Motor de IA ──
    st.markdown('<p class="sidebar-label">⚙️ Motor de IA</p>', unsafe_allow_html=True)
    modo = st.radio(
        "Motor",
        ["API (Groq Cloud)", "Local (Ollama)"],
        label_visibility="collapsed",
    )

    api_key = ""
    if modo == "API (Groq Cloud)":
        clave_entorno = os.getenv("GROQ_API_KEY")
        if clave_entorno:
            api_key = clave_entorno
            if st.checkbox("Usar otra clave"):
                api_key = st.text_input("🔑 Nueva API Key", type="password")
        else:
            api_key = st.text_input("🔑 Introduce API Key", type="password")

        modelo_seleccionado = st.selectbox(
            "Modelo",
            ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
            label_visibility="collapsed",
        )
    else:
        st.info("Ejecuta: `ollama run llama3.2:1b`")
        modelo_seleccionado = st.text_input(
            "Modelo Local", value="llama3.2:1b", label_visibility="collapsed"
        )

    st.markdown("---")

    # ── Conexiones ──
    st.markdown('<p class="sidebar-label">🔌 Conexiones</p>', unsafe_allow_html=True)

    groq_ok = bool(os.getenv("GROQ_API_KEY")) or bool(api_key)
    serper_ok = bool(os.getenv("SERPER_API_KEY"))

    if groq_ok:
        st.markdown(
            '<div class="status-pill ok">● GROQ API conectada</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="status-pill warn">○ GROQ API sin configurar</div>',
            unsafe_allow_html=True,
        )

    if serper_ok:
        st.markdown(
            '<div class="status-pill ok">● SERPER API conectada</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="status-pill warn">○ SERPER API sin configurar</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    if st.button("🗑️ Nueva Sesión", use_container_width=True):
        for key, val in defaults.items():
            st.session_state[key] = val
        st.rerun()


# ═══════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════
banner_path = "assets/banner_header.png"

if os.path.exists(banner_path):
    st.image(banner_path, use_container_width=True)

st.markdown(
    """
    <div class="app-header">
        <div class="app-header-text">
            <h1>CV SCAN AI</h1>
            <p>Análisis inteligente de perfiles & agencia de colocación con IA</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════
# KPI STRIP
# ═══════════════════════════════════════════════════════════════
cv_status = "Cargado" if st.session_state.texto_pdf else "Sin cargar"
cv_icon = "✅" if st.session_state.texto_pdf else "📄"
motor_icon = "☁️" if modo == "API (Groq Cloud)" else "🖥️"
motor_label = modelo_seleccionado.split("-")[0].capitalize() if modelo_seleccionado else "—"
agent_status = "Completado" if st.session_state.crew_resultado else "En espera"
agent_icon = "🎯" if st.session_state.crew_resultado else "🤖"

st.markdown(
    f"""
    <div class="kpi-strip">
        <div class="kpi-card">
            <div class="kpi-icon">{cv_icon}</div>
            <p class="kpi-value">{cv_status}</p>
            <p class="kpi-label">Documento CV</p>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">{motor_icon}</div>
            <p class="kpi-value">{motor_label}</p>
            <p class="kpi-label">Motor de IA</p>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">{agent_icon}</div>
            <p class="kpi-value">{agent_status}</p>
            <p class="kpi-label">Agentes CrewAI</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════════
# ZONA DE CARGA
# ═══════════════════════════════════════════════════════════════
with st.container(border=True):
    col_upload, col_btn = st.columns([3, 1], gap="medium")

    with col_upload:
        pdf_entrada = st.file_uploader(
            "Arrastra tu CV aquí o haz clic para seleccionar (PDF)",
            type=["pdf"],
            label_visibility="visible",
        )

    with col_btn:
        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
        boton_analisis = st.button("⚡ Analizar Perfil", use_container_width=True)

if pdf_entrada:
    texto_nuevo = utils.sacar_texto_pdf(pdf_entrada)
    if texto_nuevo != st.session_state.texto_pdf:
        st.session_state.texto_pdf = texto_nuevo
        st.session_state.nombre_pdf = pdf_entrada.name
        st.session_state.analisis_realizado = ""
        st.session_state.crew_resultado = ""
        
        # ─── Extraer automáticamente datos estructurados del CV ───
        try:
            with st.spinner("📋 Extrayendo datos de tu CV..."):
                extractor = ExtractorCV()
                st.session_state.datos_cv_extraidos = extractor.extraer_datos_estructurados(texto_nuevo)
                
                if st.session_state.datos_cv_extraidos:
                    nombre = st.session_state.datos_cv_extraidos.get("nombre", "Candidato")
                    st.toast(f"✅ Perfil de {nombre} cargado con éxito", icon="👤")
                else:
                    st.toast("✅ Documento cargado con éxito", icon="📄")
        except Exception as e:
            logger.warning(f"No se pudieron extraer datos automáticos: {e}")
            st.session_state.datos_cv_extraidos = {}
            st.toast("✅ Documento cargado con éxito", icon="📄")


# ═══════════════════════════════════════════════════════════════
# TRES PESTAÑAS: Reporte · Agencia CrewAI · Chat
# ═══════════════════════════════════════════════════════════════
tab_reporte, tab_crew, tab_chat = st.tabs([
    "📊 Reporte Ejecutivo",
    "🤖 Agencia CrewAI",
    "💬 Chat Asistente",
])

# ─── TAB 1: Reporte Ejecutivo (streaming directo) ────────────
with tab_reporte:
    if boton_analisis:
        if not st.session_state.texto_pdf:
            st.error("⚠️ Por favor, sube primero un PDF.")
        else:
            # Recuperar conocimiento experto del RAG
            contexto_expertos = consultar_rag(
                "mejores prácticas CV formato ATS estructura logros verbos de acción",
                coleccion_rag,
            )

            bloque_rag = ""
            if contexto_expertos:
                bloque_rag = (
                    "\n\nUsa el siguiente CONOCIMIENTO EXPERTO como base "
                    "para tu crítica y recomendaciones:\n"
                    f"{contexto_expertos}"
                )

            prompt_sistema = f"""
            Eres un experto senior en recursos humanos.
            {bloque_rag}

            Analiza el CV proporcionado y genera un informe detallado con:
            1. Nota 0-10 calidad CV.
            2. Puntos fuertes.
            3. Áreas de mejora (comparando con el conocimiento experto).
            4. Recomendaciones de redacción (basado en verbos de acción).
            5. Adecuación (claridad/diseño).
            6. Competencias técnicas/blandas detectadas.
            7. Roles adecuados.
            Usa Markdown claro. CV:
            {st.session_state.texto_pdf[:6000]}
            """

            mensajes_temp = [{"role": "user", "content": prompt_sistema}]
            placeholder = st.empty()
            placeholder.markdown("⏳ **Consultando base de conocimientos y analizando perfil...**")

            resultado_texto = ""

            if modo == "API (Groq Cloud)":
                if not api_key:
                    st.error("❌ Falta la API Key")
                else:
                    stream = utils.consultar_groq(
                        modelo_seleccionado, mensajes_temp, api_key
                    )
                    if stream:
                        for chunk in stream:
                            if chunk.choices[0].delta.content:
                                resultado_texto += chunk.choices[0].delta.content
                                placeholder.markdown(resultado_texto)
            else:
                stream = utils.consultar_local_ollama(
                    modelo_seleccionado, mensajes_temp
                )
                if stream:
                    for chunk in stream:
                        resultado_texto += chunk
                        placeholder.markdown(resultado_texto)

            st.session_state.analisis_realizado = resultado_texto
            st.rerun()

    elif st.session_state.analisis_realizado:
        st.markdown(st.session_state.analisis_realizado)
    else:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-state-icon">📊</div>
                <h4>Reporte Ejecutivo</h4>
                <p>Sube un CV y pulsa <strong>⚡ Analizar Perfil</strong> para generar un informe detallado con puntuación, fortalezas y recomendaciones.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─── TAB 2: Agencia CrewAI (multi-agente) ────────────────────
with tab_crew:
    st.markdown(
        "Lanza los **4 agentes de CrewAI** para buscar ofertas reales, "
        "investigar empresas y generar mensajes de postulación personalizados."
    )

    col_name, col_launch = st.columns([3, 1])
    with col_name:
        nombre_estudiante = st.text_input(
            "👤 Nombre del estudiante",
            value="",
            placeholder="Ej: María García López",
        )
    with col_launch:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        boton_crew = st.button(
            "🚀 Lanzar Agencia",
            use_container_width=True,
            disabled=st.session_state.crew_running,
        )

    if boton_crew:
        if not st.session_state.texto_pdf:
            st.error("⚠️ Sube un CV primero.")
        elif not nombre_estudiante.strip():
            st.error("⚠️ Introduce el nombre del estudiante.")
        elif not groq_ok:
            st.error("❌ Se necesita GROQ_API_KEY para los agentes.")
        elif not serper_ok:
            st.error("❌ Se necesita SERPER_API_KEY para las búsquedas web.")
        else:
            st.session_state.crew_running = True
            st.session_state.crew_resultado = ""
            st.session_state.crew_error = ""

            with st.spinner("🤖 Los agentes están trabajando... esto puede tardar varios minutos."):
                try:
                    from core.agencia_crew import AgenciaColocacion

                    agencia = AgenciaColocacion()
                    datos = {
                        "nombre_estudiante": nombre_estudiante.strip(),
                        "cv_text": st.session_state.texto_pdf[:6000],
                    }
                    resultado = agencia.crew().kickoff(inputs=datos)
                    st.session_state.crew_resultado = str(resultado)

                except Exception as exc:
                    st.session_state.crew_error = str(exc)

                finally:
                    st.session_state.crew_running = False

            st.rerun()

    # Mostrar resultado o error
    if st.session_state.crew_error:
        st.error(f"❌ Error de la agencia: {st.session_state.crew_error}")
        st.info(
            "💡 Esto puede deberse al límite de tokens del tier gratuito de Groq. "
            "Espera unos minutos e inténtalo de nuevo."
        )

    if st.session_state.crew_resultado:
        st.success("✅ ¡Agencia completada con éxito!")
        st.markdown("### 📝 Reporte de Postulación")
        st.markdown(st.session_state.crew_resultado)

        # Mostrar el archivo si existe
        if os.path.exists("reporte_postulacion.md"):
            with open("reporte_postulacion.md", "r", encoding="utf-8") as f:
                contenido_md = f.read()
            st.download_button(
                "📥 Descargar reporte_postulacion.md",
                data=contenido_md,
                file_name="reporte_postulacion.md",
                mime="text/markdown",
            )

    if (
        not st.session_state.crew_resultado
        and not st.session_state.crew_error
        and not st.session_state.crew_running
    ):
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-state-icon">🤖</div>
                <h4>Agencia de Colocación</h4>
                <p>Sube un CV, escribe tu nombre y pulsa <strong>🚀 Lanzar Agencia</strong> para que 4 agentes busquen ofertas y redacten postulaciones.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─── TAB 3: Chat Asistente ───────────────────────────────────
with tab_chat:
    ALTURA_CHAT = 450
    chat_container = st.container(height=ALTURA_CHAT, border=True)

    with chat_container:
        if not st.session_state.texto_pdf:
            st.markdown(
                """
                <div class="empty-state">
                    <div class="empty-state-icon">💬</div>
                    <h4>Chat Asistente</h4>
                    <p>Sube un CV para empezar a chatear. Podrás hacer preguntas sobre el perfil del candidato.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        for msg in st.session_state.mensajes:
            avatar = "👤" if msg["role"] == "user" else "🤖"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    with st.form(key="chat_form", clear_on_submit=True):
        cols_input = st.columns([8, 2])
        with cols_input[0]:
            prompt_usuario = st.text_input(
                "Pregunta...",
                placeholder="Ej: ¿Qué habilidades tiene? ¿Qué puestos le convienen?",
                label_visibility="collapsed",
            )
        with cols_input[1]:
            boton_enviar = st.form_submit_button("Enviar ➤")

    if boton_enviar and prompt_usuario:
        if not st.session_state.texto_pdf:
            st.error("⚠️ Sube un PDF arriba.")
        else:
            st.session_state.mensajes.append(
                {"role": "user", "content": prompt_usuario}
            )

            with chat_container:
                with st.chat_message("user", avatar="👤"):
                    st.markdown(prompt_usuario)

                with st.chat_message("assistant", avatar="🤖"):
                    placeholder_resp = st.empty()
                    placeholder_funcs = st.empty()
                    respuesta_completa = ""
                    
                    # ─── INTENTAR CON FUNCTION CALLING (OpenAI) ───
                    openai_key = os.getenv("OPENAI_API_KEY")
                    
                    if openai_key:
                        try:
                            with st.spinner("🔧 Procesando con function calling..."):
                                from function_calling.manage_cv import gestionar_cv
                                
                                # Crear archivo temporal si es necesario
                                cv_temp_path = None
                                if hasattr(st.session_state, 'pdf_temp_path') and st.session_state.pdf_temp_path:
                                    cv_temp_path = st.session_state.pdf_temp_path
                                else:
                                    # Crear temp con el texto del PDF
                                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
                                        tmp.write(st.session_state.texto_pdf)
                                        cv_temp_path = tmp.name
                                    st.session_state.pdf_temp_path = cv_temp_path
                                
                                # Llamar a gestionar_cv
                                resultado_fc = gestionar_cv(prompt_usuario, cv_temp_path)
                                
                                # Mostrar funciones invocadas
                                funciones_info = resultado_fc.pop("_funciones_invocadas", [])
                                
                                if funciones_info:
                                    funcs_html = "🔧 **Funciones invocadas:**\n"
                                    for func in funciones_info:
                                        funcs_html += f"• `{func['nombre']}` → {func['resultado_chars']} chars\n"
                                    placeholder_funcs.markdown(funcs_html)
                                
                                # Extraer respuesta
                                if "respuesta_directa" in resultado_fc:
                                    respuesta_completa = resultado_fc["respuesta_directa"]
                                else:
                                    # Formatear resultado estructurado
                                    respuesta_completa = json.dumps(resultado_fc, ensure_ascii=False, indent=2)
                                
                                placeholder_resp.markdown(respuesta_completa)
                                logger.info("✅ Function calling completado exitosamente")
                                
                        except Exception as e:
                            logger.warning(f"Function calling falló: {e}. Cayendo a Groq...")
                            # Caer a Groq si falla OpenAI
                            openai_key = None
                    
                    # ─── FALLBACK: USO DE GROQ ───
                    if not openai_key:
                        # RAG dinámico
                        contexto_rag = consultar_rag(prompt_usuario, coleccion_rag)

                        # Construir contexto
                        contexto = (
                            f"Actúa como asistente de RRHH. "
                            f"Aquí tienes el contenido del CV:\n{st.session_state.texto_pdf[:6000]}"
                        )
                        
                        if st.session_state.datos_cv_extraidos:
                            datos_formatted = json.dumps(st.session_state.datos_cv_extraidos, 
                                                          ensure_ascii=False, indent=2)
                            contexto += (
                                f"\n\n📊 PERFIL ESTRUCTURADO:\n"
                                f"{datos_formatted}"
                            )
                        
                        if contexto_rag:
                            contexto += (
                                f"\n\nCONOCIMIENTO EXPERTO:\n{contexto_rag}"
                            )
                        if st.session_state.analisis_realizado:
                            contexto += (
                                f"\n\nINFORME PREVIO:\n{st.session_state.analisis_realizado}"
                            )
                        if st.session_state.crew_resultado:
                            contexto += (
                                f"\n\nRESULTADO AGENCIA:\n{st.session_state.crew_resultado}"
                            )

                        mensajes_para_enviar = [
                            {"role": "system", "content": contexto}
                        ] + st.session_state.mensajes

                        if modo == "API (Groq Cloud)":
                            if not api_key:
                                st.error("❌ API Key requerida")
                            else:
                                stream = utils.consultar_groq(
                                    modelo_seleccionado,
                                    mensajes_para_enviar,
                                    api_key,
                                )
                                if stream:
                                    for chunk in stream:
                                        if chunk.choices[0].delta.content:
                                            respuesta_completa += chunk.choices[0].delta.content
                                            placeholder_resp.markdown(respuesta_completa)
                        else:
                            stream = utils.consultar_local_ollama(
                                modelo_seleccionado, mensajes_para_enviar
                            )
                            if stream:
                                for chunk in stream:
                                    respuesta_completa += chunk
                                    placeholder_resp.markdown(respuesta_completa)

                    st.session_state.mensajes.append(
                        {"role": "assistant", "content": respuesta_completa}
                    )
            st.rerun()