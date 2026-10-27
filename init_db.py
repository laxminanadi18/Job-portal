import os
import sys
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def seed_sample_data(conn, is_sqlite=True):
    placeholder = "?" if is_sqlite else "%s"
    cur = conn.cursor()

    # Passwords hashed with generate_password_hash
    hashed_pwd = generate_password_hash("password123")

    # 1. Sample Users (1 Employer, 1 Job Seeker)
    sample_users = [
        ("TechCorp Recruiter", "employer@example.com", hashed_pwd, "employer"),
        ("Rahul Sharma", "seeker@example.com", hashed_pwd, "jobseeker"),
    ]

    for name, email, pwd, role in sample_users:
        try:
            cur.execute(
                f"INSERT INTO users (name, email, password_hash, role) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})",
                (name, email, pwd, role)
            )
        except Exception:
            pass  # User might already exist

    # Get employer id
    cur.execute(
        f"SELECT id FROM users WHERE email = {placeholder}",
        ("employer@example.com",)
    )
    employer_row = cur.fetchone()
    employer_id = employer_row[0] if employer_row else 1

    # 2. Sample Jobs
    sample_jobs = [
        (
            employer_id,
            "Full Stack Python Developer",
            "TechCorp Solutions",
            "Bangalore (Hybrid)",
            "Full-time",
            "₹6,00,000 - ₹9,00,000 PA",
            "Looking for a skilled Python & Flask developer with experience in MySQL, REST APIs, and modern frontend templates."
        ),
        (
            employer_id,
            "Frontend Web Developer",
            "TechCorp Solutions",
            "Remote",
            "Full-time",
            "₹4,50,000 - ₹7,00,000 PA",
            "We are hiring a creative Frontend Developer proficient in HTML5, CSS3, JavaScript, and responsive design."
        ),
        (
            employer_id,
            "Software Intern",
            "TechCorp Solutions",
            "Hyderabad",
            "Internship",
            "₹20,000 / month",
            "Exciting 6-month internship for pre-final and final year college students with basic knowledge of Python and SQL."
        ),
    ]

    for job in sample_jobs:
        cur.execute(
            f"""INSERT INTO jobs (employer_id, title, company, location, job_type, salary, description)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})""",
            job
        )

    conn.commit()
    print("[SUCCESS] Sample users and job listings seeded successfully!")


def init_sqlite():
    db_path = BASE_DIR / "online_job_portal.db"
    print(f"[INFO] Initializing SQLite database at: {db_path}")
    conn = sqlite3.connect(str(db_path))
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
    seed_sample_data(conn, is_sqlite=True)
    conn.close()
    print("[SUCCESS] SQLite database initialized and ready!")


def init_mysql():
    import mysql.connector

    host = os.getenv("DB_HOST", "localhost")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "online_job_portal")

    print(f"[INFO] Connecting to MySQL server at {host} as user '{user}'...")
    try:
        # First connect without specifying database to create database if not exists
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.commit()
        cur.close()
        conn.close()

        # Now connect to the database
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )
        cur = conn.cursor()

        # Read schema.sql
        schema_file = BASE_DIR / "schema.sql"
        if schema_file.exists():
            with open(schema_file, "r", encoding="utf-8") as f:
                statements = f.read().split(";")
                for stmt in statements:
                    stmt = stmt.strip()
                    if stmt:
                        cur.execute(stmt)
            conn.commit()
            print(f"[SUCCESS] Database '{db_name}' and tables created from schema.sql!")

        seed_sample_data(conn, is_sqlite=False)
        conn.close()
        print("[SUCCESS] MySQL database initialized and ready!")

    except Exception as exc:
        print(f"[ERROR] Could not connect to MySQL: {exc}")
        print("\nTroubleshooting tips:")
        print("1. If using XAMPP, open XAMPP Control Panel and start the 'MySQL' service.")
        print("2. Check the DB_PASSWORD in your .env file.")
        print("3. Alternatively, you can use SQLite by setting DB_ENGINE=sqlite in .env")
        sys.exit(1)


if __name__ == "__main__":
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "auto"

    if mode in ("--mysql", "-m", "mysql"):
        init_mysql()
    elif mode in ("--sqlite", "-s", "sqlite"):
        init_sqlite()
    else:
        # Auto: try MySQL, if it fails, init SQLite
        try:
            print("[INFO] Attempting to initialize MySQL...")
            init_mysql()
        except SystemExit:
            print("\n[INFO] Falling back to SQLite for instant local development...")
            init_sqlite()
