"""
Sistema de diseño visual — CV SCAN AI.

Tema premium SaaS 2026: glassmorphism, Inter typography,
paleta Slate extendida con acentos cyan/violet.
"""

import streamlit as st

# ─── Design Tokens ────────────────────────────────────────────
BRAND_PRIMARY = "#00E5FF"
BRAND_SECONDARY = "#2979FF"
BG_BASE = "#030816"
BG_SURFACE = "#0F172A"

SLATE = {
    950: "#020617",
    900: "#0F172A",
    800: "#1E293B",
    700: "#334155",
    600: "#475569",
    400: "#94A3B8",
    200: "#E2E8F0",
    50: "#F8FAFC",
}

ACCENT_VIOLET = "#8B5CF6"
ACCENT_TEAL = "#14B8A6"

SUCCESS = "#10B981"
ERROR = "#EF4444"
WARNING = "#F59E0B"
INFO = "#3B82F6"


def configurar_pagina() -> None:
    """Configura la página de Streamlit con el tema de la app."""
    st.set_page_config(
        page_title="CV SCAN AI — Agencia Inteligente",
        layout="wide",
        page_icon="assets/logo_icon.png",
        initial_sidebar_state="expanded",
    )


def cargar_css() -> None:
    """Inyecta el sistema de diseño completo (CSS custom properties + componentes)."""
    st.markdown("""
    <style>
        /* ================================================
           0. GOOGLE FONTS
           ================================================ */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

        /* ================================================
           1. GLOBAL RESET & BASE
           ================================================ */
        html, body, [class*="css"], .stApp,
        .stMarkdown, .stMarkdown p, .stMarkdown li,
        .stTextInput label, .stSelectbox label,
        .stRadio label, .stFileUploader label,
        .stCheckbox label, .stNumberInput label,
        [data-testid="stWidgetLabel"], [data-testid="stMarkdownContainer"] p {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif !important;
        }

        code, pre, .stCode, [data-testid="stCode"] {
            font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace !important;
        }

        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 3rem !important;
            max-width: 1200px !important;
        }

        /* Hide default chrome */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stHeader"] {
            background: linear-gradient(180deg, rgba(3,8,22,0.95) 0%, rgba(3,8,22,0) 100%) !important;
            backdrop-filter: blur(8px);
        }

        /* ================================================
           2. TYPOGRAPHY
           ================================================ */
        h1 {
            font-size: 1.75rem !important;
            font-weight: 800 !important;
            letter-spacing: -0.03em !important;
            color: #F8FAFC !important;
            line-height: 1.2 !important;
        }
        h2 {
            font-size: 1.35rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em !important;
            color: #F8FAFC !important;
            line-height: 1.3 !important;
        }
        h3 {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            letter-spacing: -0.01em !important;
            color: #E2E8F0 !important;
        }
        p, li, span {
            font-size: 0.938rem !important;
            line-height: 1.65 !important;
            color: #E2E8F0 !important;
        }

        /* ================================================
           3. SIDEBAR
           ================================================ */
        [data-testid="stSidebar"] {
            background-color: #020617 !important;
            border-right: 1px solid rgba(30, 41, 59, 0.6) !important;
        }
        [data-testid="stSidebar"] .stMarkdown hr {
            border-color: rgba(30, 41, 59, 0.5) !important;
            margin: 1.25rem 0 !important;
        }

        /* Sidebar section labels */
        .sidebar-label {
            font-size: 0.68rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.1em !important;
            text-transform: uppercase !important;
            color: #94A3B8 !important;
            margin-bottom: 0.5rem !important;
            padding-left: 2px !important;
        }

        /* Status pills */
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.78rem;
            font-weight: 500;
            padding: 4px 12px;
            border-radius: 20px;
            margin: 2px 0;
        }
        .status-pill.ok {
            background: rgba(16, 185, 129, 0.12);
            color: #10B981;
            border: 1px solid rgba(16, 185, 129, 0.2);
        }
        .status-pill.warn {
            background: rgba(245, 158, 11, 0.12);
            color: #F59E0B;
            border: 1px solid rgba(245, 158, 11, 0.2);
        }

        /* ================================================
           4. CARDS / CONTAINERS — GLASSMORPHISM
           ================================================ */
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"],
        [data-testid="stExpander"] {
            background: rgba(15, 23, 42, 0.55) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(148, 163, 184, 0.07) !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25),
                        0 1px 3px rgba(0, 0, 0, 0.15) !important;
        }

        /* Bordered containers */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: rgba(148, 163, 184, 0.08) !important;
            border-radius: 12px !important;
            background: rgba(15, 23, 42, 0.4) !important;
        }

        /* ================================================
           5. BUTTONS
           ================================================ */
        .stButton > button {
            background: linear-gradient(135deg, #00E5FF 0%, #2979FF 100%) !important;
            color: #020617 !important;
            border: none !important;
            padding: 10px 24px !important;
            font-size: 0.875rem !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            letter-spacing: 0.02em !important;
            border-radius: 10px !important;
            cursor: pointer !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 2px 8px rgba(0, 229, 255, 0.15),
                        0 1px 2px rgba(0, 0, 0, 0.1) !important;
        }
        .stButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 16px rgba(0, 229, 255, 0.3),
                        0 2px 4px rgba(0, 0, 0, 0.15) !important;
            filter: brightness(1.08) !important;
        }
        .stButton > button:active {
            transform: translateY(0px) !important;
        }

        /* Download button */
        .stDownloadButton > button {
            background: rgba(15, 23, 42, 0.6) !important;
            border: 1px solid rgba(0, 229, 255, 0.25) !important;
            color: #00E5FF !important;
        }
        .stDownloadButton > button:hover {
            background: rgba(0, 229, 255, 0.08) !important;
            border-color: rgba(0, 229, 255, 0.5) !important;
        }

        /* Form submit button */
        .stFormSubmitButton > button {
            background: linear-gradient(135deg, #00E5FF 0%, #2979FF 100%) !important;
            color: #020617 !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 2px 8px rgba(0, 229, 255, 0.15) !important;
        }
        .stFormSubmitButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 16px rgba(0, 229, 255, 0.3) !important;
        }

        /* ================================================
           6. INPUTS & SELECT
           ================================================ */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input {
            background-color: #020617 !important;
            color: #E2E8F0 !important;
            border: 1px solid #1E293B !important;
            border-radius: 10px !important;
            padding: 12px 16px !important;
            font-size: 0.875rem !important;
            font-family: 'Inter', sans-serif !important;
            transition: all 0.2s ease !important;
        }
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus {
            border-color: rgba(0, 229, 255, 0.4) !important;
            box-shadow: 0 0 0 3px rgba(0, 229, 255, 0.08) !important;
            outline: none !important;
        }
        .stTextInput > div > div > input::placeholder {
            color: #475569 !important;
        }

        .stSelectbox > div > div {
            background-color: #020617 !important;
            border: 1px solid #1E293B !important;
            border-radius: 10px !important;
        }

        /* Radio buttons */
        .stRadio > div {
            gap: 0.5rem !important;
        }
        .stRadio > div > label {
            background: rgba(15, 23, 42, 0.4) !important;
            border: 1px solid #1E293B !important;
            border-radius: 8px !important;
            padding: 8px 14px !important;
            transition: all 0.15s ease !important;
        }
        .stRadio > div > label:hover {
            border-color: rgba(0, 229, 255, 0.3) !important;
            background: rgba(0, 229, 255, 0.04) !important;
        }

        /* ================================================
           7. TABS
           ================================================ */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0px !important;
            background: transparent !important;
            border-bottom: 1px solid #1E293B !important;
            padding: 0 !important;
        }
        .stTabs [data-baseweb="tab"] {
            font-family: 'Inter', sans-serif !important;
            font-weight: 500 !important;
            font-size: 0.875rem !important;
            color: #94A3B8 !important;
            padding: 12px 20px !important;
            border: none !important;
            background: transparent !important;
            border-bottom: 2px solid transparent !important;
            transition: all 0.2s ease !important;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: #E2E8F0 !important;
            background: rgba(0, 229, 255, 0.03) !important;
        }
        .stTabs [aria-selected="true"] {
            color: #00E5FF !important;
            border-bottom: 2px solid #00E5FF !important;
            background: transparent !important;
        }
        .stTabs [data-baseweb="tab-highlight"] {
            display: none !important;
        }
        .stTabs [data-baseweb="tab-border"] {
            display: none !important;
        }

        /* ================================================
           8. CHAT MESSAGES
           ================================================ */
        [data-testid="stChatMessage"] {
            padding: 1rem 1.25rem !important;
            margin-bottom: 12px !important;
            border-radius: 12px !important;
            transition: background 0.15s ease !important;
        }
        /* User messages */
        [data-testid="stChatMessage"]:nth-child(odd) {
            background: rgba(15, 23, 42, 0.5) !important;
            border-left: 3px solid #00E5FF !important;
            border-top: none !important;
            border-right: none !important;
            border-bottom: none !important;
        }
        /* Assistant messages */
        [data-testid="stChatMessage"]:nth-child(even) {
            background: rgba(2, 6, 23, 0.6) !important;
            border-left: 3px solid #8B5CF6 !important;
            border-top: none !important;
            border-right: none !important;
            border-bottom: none !important;
        }

        /* ================================================
           9. FILE UPLOADER
           ================================================ */
        [data-testid="stFileUploader"] {
            border-radius: 12px !important;
        }
        [data-testid="stFileUploader"] > div {
            border-radius: 12px !important;
        }
        [data-testid="stFileUploaderDropzone"] {
            background: rgba(2, 6, 23, 0.5) !important;
            border: 1.5px dashed #334155 !important;
            border-radius: 12px !important;
            padding: 2rem !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="stFileUploaderDropzone"]:hover {
            border-color: #00E5FF !important;
            background: rgba(0, 229, 255, 0.03) !important;
        }

        /* ================================================
           10. ALERTS
           ================================================ */
        .stSuccess {
            background-color: rgba(16, 185, 129, 0.08) !important;
            border: 1px solid rgba(16, 185, 129, 0.2) !important;
            border-radius: 10px !important;
            color: #10B981 !important;
        }
        .stError {
            background-color: rgba(239, 68, 68, 0.08) !important;
            border: 1px solid rgba(239, 68, 68, 0.2) !important;
            border-radius: 10px !important;
        }
        .stWarning {
            background-color: rgba(245, 158, 11, 0.08) !important;
            border: 1px solid rgba(245, 158, 11, 0.2) !important;
            border-radius: 10px !important;
        }
        .stInfo {
            background-color: rgba(59, 130, 246, 0.08) !important;
            border: 1px solid rgba(59, 130, 246, 0.2) !important;
            border-radius: 10px !important;
        }

        /* Toast */
        .stToast {
            background-color: #0F172A !important;
            border: 1px solid rgba(0, 229, 255, 0.15) !important;
            border-radius: 10px !important;
            color: #E2E8F0 !important;
            backdrop-filter: blur(12px) !important;
        }

        /* ================================================
           11. SPINNER
           ================================================ */
        .stSpinner > div {
            border-color: #00E5FF transparent transparent transparent !important;
        }

        /* ================================================
           12. METRICS (KPI cards)
           ================================================ */
        .kpi-strip {
            display: flex;
            gap: 16px;
            margin: 0 0 1.5rem 0;
        }
        .kpi-card {
            flex: 1;
            background: rgba(15, 23, 42, 0.55);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(148, 163, 184, 0.07);
            border-radius: 12px;
            padding: 18px 20px;
            text-align: center;
            transition: all 0.2s ease;
        }
        .kpi-card:hover {
            border-color: rgba(0, 229, 255, 0.15);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        }
        .kpi-icon {
            font-size: 1.5rem;
            margin-bottom: 6px;
        }
        .kpi-value {
            font-size: 0.85rem;
            font-weight: 600;
            color: #F8FAFC;
            margin: 0;
        }
        .kpi-label {
            font-size: 0.7rem;
            font-weight: 500;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin: 2px 0 0 0;
        }

        /* ================================================
           13. HEADER
           ================================================ */
        .app-header {
            display: flex;
            align-items: center;
            gap: 18px;
            padding: 0.5rem 0 1rem 0;
            margin-bottom: 0.5rem;
        }
        .app-header img {
            width: 52px;
            height: 52px;
            border-radius: 12px;
            object-fit: contain;
        }
        .app-header-text h1 {
            margin: 0 !important;
            padding: 0 !important;
            font-size: 1.6rem !important;
            background: linear-gradient(135deg, #00E5FF 0%, #2979FF 60%, #8B5CF6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .app-header-text p {
            margin: 2px 0 0 0 !important;
            font-size: 0.82rem !important;
            color: #94A3B8 !important;
            font-weight: 400 !important;
        }

        /* ================================================
           14. EMPTY STATES
           ================================================ */
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #475569;
        }
        .empty-state-icon {
            font-size: 2.8rem;
            margin-bottom: 12px;
            opacity: 0.6;
        }
        .empty-state h4 {
            font-size: 1rem !important;
            font-weight: 600 !important;
            color: #94A3B8 !important;
            margin: 0 0 6px 0 !important;
        }
        .empty-state p {
            font-size: 0.82rem !important;
            color: #475569 !important;
            max-width: 320px;
            margin: 0 auto !important;
        }

        /* ================================================
           15. SCROLLBAR
           ================================================ */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: #1E293B;
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #334155;
        }

        /* ================================================
           16. MISC REFINEMENTS
           ================================================ */
        /* Dividers */
        hr {
            border-color: rgba(30, 41, 59, 0.5) !important;
        }

        /* Links */
        a {
            color: #00E5FF !important;
            text-decoration: none !important;
            transition: opacity 0.15s !important;
        }
        a:hover {
            opacity: 0.8 !important;
        }

        /* Progress bar */
        .stProgress > div > div > div {
            background: linear-gradient(90deg, #00E5FF, #2979FF) !important;
            border-radius: 4px !important;
        }

        /* Checkbox */
        .stCheckbox label span {
            font-size: 0.85rem !important;
        }
    </style>
    """, unsafe_allow_html=True)
