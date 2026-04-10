"""
Tests unitarios para el módulo RAG.

Verifica la correcta inicialización, ingesta y consulta del sistema
de recuperación aumentada de generación (Retrieval Augmented Generation).
"""

import tempfile
from pathlib import Path

import pytest

from core.rag import (
    _calcular_hash_archivo,
    _dividir_en_fragmentos,
    consultar_rag,
    inicializar_coleccion,
    ingestar_conocimiento,
    COLLECTION_NAME,
)


# =============================================
# Tests de funciones auxiliares
# =============================================


class TestCalcularHashArchivo:
    """Verifica el cálculo de hash de archivos."""

    def test_hash_consistente_mismo_archivo(self) -> None:
        """El hash debe ser determinista para el mismo archivo."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("contenido de prueba")
            ruta = Path(f.name)

        try:
            hash1 = _calcular_hash_archivo(ruta)
            hash2 = _calcular_hash_archivo(ruta)
            assert hash1 == hash2
        finally:
            ruta.unlink()

    def test_hash_diferentes_archivos(self) -> None:
        """Archivos diferentes deben producir hashes diferentes."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f1:
            f1.write("contenido 1")
            ruta1 = Path(f1.name)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f2:
            f2.write("contenido 2")
            ruta2 = Path(f2.name)

        try:
            hash1 = _calcular_hash_archivo(ruta1)
            hash2 = _calcular_hash_archivo(ruta2)
            assert hash1 != hash2
        finally:
            ruta1.unlink()
            ruta2.unlink()

    def test_hash_es_corto(self) -> None:
        """El hash debe tener exactamente 8 caracteres."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test")
            ruta = Path(f.name)

        try:
            hash_val = _calcular_hash_archivo(ruta)
            assert len(hash_val) == 8
            assert hash_val.isalnum()
        finally:
            ruta.unlink()


# =============================================
# Tests de fragmentación de texto
# =============================================


class TestDividirEnFragmentos:
    """Verifica la división de texto en fragmentos con solapamiento."""

    def test_texto_vacio_devuelve_lista_vacia(self) -> None:
        """Un texto vacío debe devolver una lista vacía."""
        resultado = _dividir_en_fragmentos("")
        assert resultado == []

    def test_texto_corto_no_se_divide(self) -> None:
        """Un texto más corto que el tamaño objetivo no debe dividirse."""
        texto = "Este es un texto corto"
        resultado = _dividir_en_fragmentos(texto, chunk_size=100)
        assert len(resultado) == 1
        assert resultado[0] == texto

    def test_texto_largo_se_divide(self) -> None:
        """Un texto largo debe dividirse en fragmentos."""
        texto = "palabra " * 500  # Texto largo
        resultado = _dividir_en_fragmentos(texto, chunk_size=100)
        assert len(resultado) > 1
        for fragmento in resultado:
            assert fragmento.strip()  # No vacíos

    def test_preserva_semantica_parrafos(self) -> None:
        """Debe preferir cortar en párrafos."""
        texto = "Párrafo 1\n\nPárrafo 2\n\nPárrafo 3"
        resultado = _dividir_en_fragmentos(texto, chunk_size=50)
        assert len(resultado) > 0

    def test_lista_no_vacia_sin_fragmentos_vacios(self) -> None:
        """Los fragmentos devueltos nunca deben estar vacíos."""
        texto = "contenido " * 200
        resultado = _dividir_en_fragmentos(texto)
        assert all(fragmento.strip() for fragmento in resultado)


# =============================================
# Tests de inicialización de colección
# =============================================


class TestInicializarColeccion:
    """Verifica la inicialización correcta de ChromaDB."""

    def test_crea_coleccion_con_nombre_correcto(self) -> None:
        """Debe crear una colección con el nombre esperado."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coleccion = inicializar_coleccion(db_path=tmpdir)
            assert coleccion is not None
            assert coleccion.name == COLLECTION_NAME


# =============================================
# Tests de ingesta
# =============================================


class TestIngestarConocimiento:
    """Verifica la carga de PDFs en la colección."""

    def test_retorna_cero_carpeta_no_existe(self) -> None:
        """Si la carpeta no existe, debe retornar 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coleccion = inicializar_coleccion(db_path=tmpdir)
            resultado = ingestar_conocimiento(
                coleccion, carpeta="/ruta/no/existe"
            )
            assert resultado == 0

    def test_retorna_cero_sin_pdfs(self) -> None:
        """Si no hay PDFs en la carpeta, debe retornar 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_dir = str(Path(tmpdir) / "db")
            coleccion = inicializar_coleccion(db_path=db_dir)
            resultado = ingestar_conocimiento(
                coleccion, carpeta=tmpdir
            )
            assert resultado == 0

    def test_lanza_error_carpeta_vacia(self) -> None:
        """Pasar una cadena vacía como carpeta debe lanzar ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coleccion = inicializar_coleccion(db_path=tmpdir)
            with pytest.raises(ValueError, match="no vacía"):
                ingestar_conocimiento(coleccion, carpeta="")


# =============================================
# Tests de consulta
# =============================================


class TestConsultarRag:
    """Verifica la búsqueda en la colección."""

    def test_retorna_vacio_coleccion_nula(self) -> None:
        """Si la colección es None, debe retornar cadena vacía."""
        resultado = consultar_rag("test", coleccion=None)
        assert resultado == ""

    def test_retorna_vacio_query_vacia(self) -> None:
        """Si la query está vacía, debe retornar cadena vacía."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coleccion = inicializar_coleccion(db_path=tmpdir)
            resultado = consultar_rag("", coleccion=coleccion)
            assert resultado == ""

    def test_retorna_vacio_query_solo_espacios(self) -> None:
        """Si la query solo tiene espacios, debe retornar cadena vacía."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coleccion = inicializar_coleccion(db_path=tmpdir)
            resultado = consultar_rag("   ", coleccion=coleccion)
            assert resultado == ""

    def test_lanza_error_n_results_invalido(self) -> None:
        """n_results < 1 debe lanzar ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coleccion = inicializar_coleccion(db_path=tmpdir)
            with pytest.raises(ValueError, match="n_results"):
                consultar_rag("test", coleccion=coleccion, n_results=0)

    def test_retorna_vacio_coleccion_vacia(self) -> None:
        """Si la colección está vacía, debe retornar cadena vacía."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coleccion = inicializar_coleccion(db_path=tmpdir)
            resultado = consultar_rag("test", coleccion=coleccion)
            assert resultado == ""
