"""
Módulo RAG (Retrieval Augmented Generation) para CV SCAN AI.

Proporciona funciones para inicializar, ingestar y consultar
una base de datos vectorial de conocimiento experto sobre CVs usando ChromaDB.
"""

import hashlib
import logging
from pathlib import Path
from typing import Optional

import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

# =============================================
# Configuración
# =============================================

COLLECTION_NAME = "cv_experto"
MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 300  # palabras aproximadas
CHUNK_OVERLAP = 50  # palabras de solapamiento

# Logger
logger = logging.getLogger(__name__)


# =============================================
# Funciones auxiliares
# =============================================


def _calcular_hash_archivo(ruta: Path) -> str:
    """
    Calcula el hash corto (8 caracteres) de un archivo.

    Args:
        ruta: Path al archivo

    Returns:
        Hash SHA256 truncado a 8 caracteres

    Raises:
        FileNotFoundError: Si el archivo no existe
        IOError: Si hay error al leer el archivo
    """
    if not ruta.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {ruta}")

    try:
        sha256_hash = hashlib.sha256()
        with open(ruta, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        # Retornar solo los primeros 8 caracteres del hash
        return sha256_hash.hexdigest()[:8]
    except IOError as e:
        logger.error(f"Error al leer archivo {ruta}: {e}")
        raise


def _dividir_en_fragmentos(
    texto: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP
) -> list[str]:
    """
    Divide un texto en fragmentos con solapamiento.

    Args:
        texto: Texto a dividir
        chunk_size: Tamaño aproximado de cada fragmento (palabras)
        overlap: Número de palabras de solapamiento entre fragmentos

    Returns:
        Lista de fragmentos (puede estar vacía si texto está vacío)
    """
    if not texto or not texto.strip():
        return []

    # Dividir en palabras
    palabras = texto.split()
    
    if len(palabras) <= chunk_size:
        return [texto]
    
    # Crear fragmentos con solapamiento
    fragmentos = []
    i = 0
    
    while i < len(palabras):
        # Tomar chunk_size palabras
        fragmento_palabras = palabras[i : i + chunk_size]
        fragmento = " ".join(fragmento_palabras)
        fragmentos.append(fragmento)
        
        # Avanzar por (chunk_size - overlap) para el siguiente fragmento
        i += chunk_size - overlap
    
    return fragmentos




# =============================================
# Funciones principales
# =============================================


def inicializar_coleccion(db_path: Optional[str] = None) -> chromadb.Collection:
    """
    Inicializa la colección ChromaDB con el modelo de embeddings.

    La colección se reutiliza en memoria si ya existe (con @st.cache_resource)
    o se realiza carga desde disco si el proyecto se reinicia.

    Args:
        db_path: Ruta personalizadado para la BD. Si es None, usa ruta por defecto.

    Returns:
        Collection de ChromaDB lista para ingesta y consultas

    Raises:
        Exception: Si hay error al inicializar ChromaDB o el modelo
    """
    try:
        # Determinar ruta de BD
        if db_path is None:
            db_dir = Path.cwd() / "db_cv_expert"
        else:
            db_dir = Path(db_path)

        # Crear directorio de base de datos si no existe
        db_dir.mkdir(parents=True, exist_ok=True)

        # Usar nueva API de ChromaDB
        client = chromadb.PersistentClient(path=str(db_dir))

        # Obtener o crear colección
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(f"Colección '{COLLECTION_NAME}' inicializada correctamente")
        return collection

    except Exception as e:
        logger.error(f"Error al inicializar ChromaDB: {e}")
        raise


def ingestar_conocimiento(coleccion: chromadb.Collection, carpeta: str) -> int:
    """
    Carga PDFs de una carpeta en la colección ChromaDB.

    Evita duplicados verificando si los documentos ya fueron ingestados.
    Utiliza hash de archivos para detectar cambios.

    Args:
        coleccion: Colección ChromaDB donde almacenar
        carpeta: Ruta a la carpeta con archivos PDF (string)

    Returns:
        Número total de fragmentos ingestados (0 si no hay PDFs o error)

    Raises:
        ValueError: Si carpeta es cadena vacía
    """
    if not isinstance(carpeta, str) or not carpeta.strip():
        raise ValueError("carpeta debe ser una cadena de texto no vacía")

    ruta_carpeta = Path(carpeta)

    # Si la ruta no existe o no es directorio, retornar 0
    if not ruta_carpeta.exists() or not ruta_carpeta.is_dir():
        logger.warning(f"Carpeta no existe o no es directorio: {carpeta}")
        return 0

    try:
        # Inicializar modelo de embeddings
        modelo = SentenceTransformer(MODEL_NAME)

        fragmentos_totales = 0

        # Procesar PDFs
        archivos_pdf = list(ruta_carpeta.glob("*.pdf"))

        if not archivos_pdf:
            logger.warning(f"No se encontraron PDFs en {carpeta}")
            return 0

        for archivo_pdf in archivos_pdf:
            try:
                # Calcular hash del archivo
                hash_archivo = _calcular_hash_archivo(archivo_pdf)

                # Verificar si ya fue ingestado
                try:
                    resultados = coleccion.get(
                        where={"hash": hash_archivo}
                    )
                    if resultados["ids"]:
                        logger.info(f"Archivo {archivo_pdf.name} ya fue ingestado, saltando...")
                        continue
                except Exception:
                    pass  # Si hay error en where, continuar

                # Extraer texto del PDF
                lector_pdf = PdfReader(archivo_pdf)
                texto_completo = ""

                for num_pagina, pagina in enumerate(lector_pdf.pages, 1):
                    try:
                        texto = pagina.extract_text()
                        if texto:
                            texto_completo += f"\n--- Página {num_pagina} ---\n{texto}"
                    except Exception as e:
                        logger.warning(f"Error extrayendo página {num_pagina}: {e}")
                        continue

                if not texto_completo.strip():
                    logger.warning(f"No se extrajo texto de {archivo_pdf.name}")
                    continue

                # Dividir en fragmentos
                fragmentos = _dividir_en_fragmentos(texto_completo)

                if not fragmentos:
                    logger.warning(f"No se generaron fragmentos para {archivo_pdf.name}")
                    continue

                # Generar embeddings
                embeddings = modelo.encode(fragmentos)

                # Añadir a la colección
                ids = [
                    f"{archivo_pdf.stem}_chunk_{i}" for i in range(len(fragmentos))
                ]

                coleccion.add(
                    ids=ids,
                    embeddings=embeddings.tolist(),
                    documents=fragmentos,
                    metadatas=[
                        {
                            "fuente": archivo_pdf.name,
                            "hash": hash_archivo,
                            "tipo": "pdf",
                        }
                        for _ in fragmentos
                    ],
                )

                fragmentos_totales += len(fragmentos)

                logger.info(
                    f"✓ {archivo_pdf.name}: {len(fragmentos)} fragmentos ingestados"
                )

            except Exception as e:
                logger.error(f"Error procesando {archivo_pdf.name}: {e}")
                continue

        logger.info(
            f"Ingesta completada: {fragmentos_totales} fragmentos ingestados"
        )

        return fragmentos_totales

    except Exception as e:
        logger.error(f"Error en ingesta de conocimiento: {e}")
        return 0


def consultar_rag(
    consulta: str, coleccion: Optional[chromadb.Collection] = None, n_results: int = 3
) -> str:
    """
    Consulta la base de datos RAG para obtener contexto relevante.

    Args:
        consulta: Texto de la consulta del usuario
        coleccion: Colección ChromaDB donde buscar (None es válido)
        n_results: Número de fragmentos a devolver (default: 3)

    Returns:
        String con fragmentos concatenados, o cadena vacía si no hay resultados

    Raises:
        ValueError: Si n_results < 1
    """
    # Validar colección
    if coleccion is None:
        return ""

    # Validar consulta
    if not isinstance(consulta, str) or not consulta.strip():
        return ""

    # Validar n_results
    if n_results < 1:
        raise ValueError("n_results debe ser mayor que 0")

    try:
        # Si la colección está vacía, retornar cadena vacía
        count = coleccion.count()
        if count == 0:
            return ""

        # Inicializar modelo para generar embedding de consulta
        modelo = SentenceTransformer(MODEL_NAME)
        embedding_consulta = modelo.encode([consulta])[0]

        # Consultar colección
        resultados = coleccion.query(
            query_embeddings=[embedding_consulta.tolist()],
            n_results=min(n_results, count),
        )

        # Extraer documentos
        documentos = resultados.get("documents", [[]])[0]

        if not documentos:
            return ""

        # Concatenar documentos en un string
        contexto = "\n---\n".join(documentos)

        logger.debug(f"Consulta RAG: '{consulta}' → {len(documentos)} resultados")

        return contexto

    except Exception as e:
        logger.error(f"Error en consulta RAG: {e}")
        return ""

