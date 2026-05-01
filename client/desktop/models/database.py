import sqlite3
import uuid
from datetime import datetime
from pathlib import Path


class Database:
    def __init__(self):
        self.db_dir = Path(__file__).parent.parent
        self.db_path = self.db_dir / "research_data.db"
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def _create_schema(self):
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id_user TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                sex TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id_session TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                timing TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id_user)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id_image TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                image_name TEXT,
                reaction_time REAL,
                true_class INTEGER,
                predicted_class INTEGER,
                FOREIGN KEY (session_id) REFERENCES sessions (id_session)
            )
        """)

        self.conn.commit()

    def create_users(self, name, sex):
        user_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO users (id_user, name, sex, created_at) VALUES (?, ?, ?, ?)",
            (user_id, name, sex, datetime.now()),
        )
        self.conn.commit()

        return user_id

    def create_session(self, user_id, timing):
        session_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO sessions (id_session, user_id, timing)
            VALUES (?, ?, ?)""",
            (session_id, user_id, timing),
        )
        self.conn.commit()

        return session_id

    def add_image(
        self, session_id, image_name, reaction_time, true_class, predicted_class
    ):
        image_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO images
            (id_image, session_id, image_name, reaction_time, true_class, predicted_class)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                image_id,
                session_id,
                image_name,
                reaction_time,
                true_class,
                predicted_class,
            ),
        )
        self.conn.commit()

        return image_id

    def get_all_results(self):
        """Получить все результаты, объединяя три таблицы"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                u.id_user,
                u.name as participant_name,
                u.sex,
                u.created_at as registration_date,
                s.id_session,
                s.timing,
                i.id_image,
                i.image_name,
                i.reaction_time,
                i.true_class,
                i.predicted_class
            FROM users u
            JOIN sessions s ON u.id_user = s.user_id
            JOIN images i ON s.id_session = i.session_id
            ORDER BY u.created_at DESC, i.image_name
        """)
        return cursor.fetchall()

    def get_statistics(self):
        """Получить статистику по ответам"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                u.id_user,
                u.name,
                u.sex,
                s.timing,
                COUNT(i.id_image) as total_images,
                SUM(CASE WHEN i.true_class = i.predicted_class THEN 1 ELSE 0 END) as correct_answers,
                AVG(i.reaction_time) as avg_reaction_time,
                SUM(CASE WHEN i.predicted_class = -1 THEN 1 ELSE 0 END) as timeouts
            FROM users u
            JOIN sessions s ON u.id_user = s.user_id
            JOIN images i ON s.id_session = i.session_id
            GROUP BY u.id_user, s.id_session
            ORDER BY u.created_at DESC
        """)
        return cursor.fetchall()
