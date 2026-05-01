# client/models/database.py
import sqlite3
import json
from datetime import datetime
from pathlib import Path


class LocalDatabase:
    def __init__(self):
        # БД будет храниться прямо в папке client
        self.db_dir = Path(__file__).parent.parent  # Путь к client/
        self.db_path = self.db_dir / "local_storage.db"

        # Создаем папку если нет (на всякий случай)
        self.db_path.parent.mkdir(exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        """Создает все нужные таблицы"""
        cursor = self.conn.cursor()

        # Таблица для исследований (твои результаты)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_results (
                id TEXT PRIMARY KEY,
                research_id TEXT NOT NULL,
                data TEXT NOT NULL,  -- JSON с результатами
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                synced_at TIMESTAMP,
                sync_status TEXT DEFAULT 'local'  -- local, synced, conflict
            )
        """)

        # Таблица метаданных исследований
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_meta (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                created_date TEXT,
                last_modified TIMESTAMP
            )
        """)

        # Очередь синхронизации
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id TEXT,
                table_name TEXT,
                action TEXT,  -- insert, update, delete
                data TEXT,
                created_at TIMESTAMP,
                synced INTEGER DEFAULT 0
            )
        """)

        self.conn.commit()

    def save_result(self, research_id, data, result_id=None):
        """Сохраняет результат исследования"""
        cursor = self.conn.cursor()

        if result_id is None:
            result_id = f"{research_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        now = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT OR REPLACE INTO research_results 
            (id, research_id, data, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (result_id, research_id, json.dumps(data), "draft", now, now),
        )

        # Добавляем в очередь синхронизации
        cursor.execute(
            """
            INSERT INTO sync_queue (record_id, table_name, action, data, created_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (result_id, "research_results", "insert", json.dumps(data), now),
        )

        self.conn.commit()
        return result_id

    def get_results_for_research(self, research_id):
        """Получает все результаты конкретного исследования"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM research_results 
            WHERE research_id = ? 
            ORDER BY updated_at DESC
        """,
            (research_id,),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "id": row["id"],
                    "data": json.loads(row["data"]),
                    "status": row["status"],
                    "sync_status": row["sync_status"],
                    "updated_at": row["updated_at"],
                }
            )
        return results

    def get_all_results(self):
        """Все результаты всех исследований"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM research_results ORDER BY updated_at DESC")

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "id": row["id"],
                    "research_id": row["research_id"],
                    "data": json.loads(row["data"]),
                    "status": row["status"],
                    "sync_status": row["sync_status"],
                }
            )
        return results

    def close(self):
        """Закрывает соединение с БД"""
        self.conn.close()
