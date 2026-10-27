import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SQLITE_DB_PATH = BASE_DIR / "online_job_portal.db"


class SQLiteCursorWrapper:
    def __init__(self, cursor, dictionary=False):
        self._cursor = cursor
        self._dictionary = dictionary

    def execute(self, query, params=None):
        query = query.replace("%s", "?")
        if params is None:
            return self._cursor.execute(query)
        return self._cursor.execute(query, params)

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        if self._dictionary:
            return dict(row)
        return row

    def fetchall(self):
        rows = self._cursor.fetchall()
        if self._dictionary:
            return [dict(r) for r in rows]
        return rows

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    def close(self):
        self._cursor.close()


class SQLiteConnectionWrapper:
    def __init__(self, connection):
        self._conn = connection

    def cursor(self, dictionary=False):
        cur = self._conn.cursor()
        return SQLiteCursorWrapper(cur, dictionary=dictionary)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def init_sqlite_db():
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('employer', 'jobseeker')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employer_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            job_type TEXT NOT NULL,
            salary TEXT,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employer_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            jobseeker_id INTEGER NOT NULL,
            resume_link TEXT,
            cover_letter TEXT,
            status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Shortlisted', 'Rejected')),
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(job_id, jobseeker_id),
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
            FOREIGN KEY (jobseeker_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()


def get_sqlite_db():
    global SQLITE_DB_PATH
    # In Vercel serverless environment, root directory is read-only; /tmp is writable
    if os.getenv("VERCEL"):
        import shutil
        tmp_db_path = Path("/tmp") / "online_job_portal.db"
        if not tmp_db_path.exists():
            bundled_db = BASE_DIR / "online_job_portal.db"
            if bundled_db.exists():
                shutil.copyfile(bundled_db, tmp_db_path)
            else:
                SQLITE_DB_PATH = tmp_db_path
                init_sqlite_db()
        SQLITE_DB_PATH = tmp_db_path

    if not SQLITE_DB_PATH.exists():
        init_sqlite_db()
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return SQLiteConnectionWrapper(conn)


def get_mysql_db():
    import mysql.connector
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "online_job_portal")
    )


def get_db():
    """
    Returns a database connection.
    Controlled by DB_ENGINE in .env:
      - 'auto' (default): tries MySQL; if unavailable, uses SQLite.
      - 'mysql': connects to MySQL.
      - 'sqlite': connects to SQLite.
    """
    engine = os.getenv("DB_ENGINE", "auto").strip().lower()

    if engine == "sqlite":
        return get_sqlite_db()

    if engine == "mysql":
        return get_mysql_db()

    # 'auto' mode: try MySQL first, fallback to SQLite
    try:
        return get_mysql_db()
    except Exception:
        return get_sqlite_db()
