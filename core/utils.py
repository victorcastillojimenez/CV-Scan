"""
Utilidades compartidas: extracción de PDF, conexión con Groq y Ollama.
"""

import json

import fitz  # PyMuPDF
import requests
import streamlit as st
from groq import Groq


def sacar_texto_pdf(archivo) -> str:
    """Extrae texto plano de un archivo PDF en memoria.

    Args:
        archivo: UploadedFile de Streamlit (buffer con método .read()).

    Returns:
        Texto extraído del PDF o mensaje de error.
    """
    try:
        doc = fitz.open(stream=archivo.read(), filetype="pdf")
        texto = ""
        for pagina in doc:
            texto += pagina.get_text()
        return texto
    except Exception as e:
        return f"Error leyendo PDF: {e}"


def consultar_groq(modelo: str, mensajes: list, api_key: str):
    """Conecta con la API de Groq y devuelve un stream.

    Args:
        modelo: Nombre del modelo (ej: llama-3.3-70b-versatile).
        mensajes: Lista de mensajes con formato OpenAI.
        api_key: Clave de API de Groq.

    Returns:
        Stream de completions o None si falla.
    """
    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model=modelo,
            messages=mensajes,
            temperature=0.7,
            max_tokens=1024,
            stream=True,
        )
        return completion
    except Exception as e:
        st.error(f"Error conectando con Groq: {e}")
        return None


def consultar_local_ollama(modelo: str, mensajes: list):
    """Conecta con servidor local Ollama y devuelve un generador.

    Args:
        modelo: Nombre del modelo local (ej: llama3.2:1b).
        mensajes: Lista de mensajes con formato OpenAI.

    Yields:
        Fragmentos de texto de la respuesta.
    """
    url = "http://localhost:11434/api/chat"
    payload = {"model": modelo, "messages": mensajes, "stream": True}

    try:
        with requests.post(url, json=payload, stream=True) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    body = json.loads(line)
                    if "message" in body:
                        yield body["message"]["content"]
    except Exception as e:
        st.error(f"Error conectando con Ollama Local: {e}")
        return None
