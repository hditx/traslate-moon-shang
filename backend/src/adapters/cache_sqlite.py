import sqlite3

from domain.entities import TranslationResult
from domain.ports import ITranslationCache


class SqliteTranslationCache(ITranslationCache):
    """Adaptador de almacenamiento persistente en SQLite para traducciones cacheadas."""

    def __init__(self, db_path: str = "translations.db"):
        self.db_path = db_path
        self._is_memory = db_path == ":memory:"
        self._shared_conn = sqlite3.connect(":memory:") if self._is_memory else None
        if self._shared_conn:
            self._shared_conn.row_factory = sqlite3.Row
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._is_memory and self._shared_conn:
            return self._shared_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS translations (
                    text_zh TEXT PRIMARY KEY,
                    pinyin TEXT NOT NULL,
                    translation_es TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            # Limpiar posibles entradas residuales simuladas de MockTranslator
            conn.execute("DELETE FROM translations WHERE translation_es LIKE '[ES] %'")
            conn.commit()
        finally:
            if not self._is_memory:
                conn.close()

    def get(self, text_zh: str) -> TranslationResult | None:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT text_zh, pinyin, translation_es FROM translations WHERE text_zh = ?",
                (text_zh.strip(),),
            )
            row = cursor.fetchone()
            if row:
                trans_es = row["translation_es"]
                if trans_es.startswith("[ES] "):
                    return None
                return TranslationResult(
                    textZh=row["text_zh"],
                    pinyin=row["pinyin"],
                    translationEs=trans_es,
                    fromCache=True,
                )
            return None
        finally:
            if not self._is_memory:
                conn.close()

    def set(self, result: TranslationResult) -> None:
        # No almacenar en caché valores temporales simulados
        if result.translation_es.startswith("[ES] "):
            return

        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO translations (text_zh, pinyin, translation_es)
                VALUES (?, ?, ?)
                """,
                (result.text_zh.strip(), result.pinyin, result.translation_es),
            )
            conn.commit()
        finally:
            if not self._is_memory:
                conn.close()

