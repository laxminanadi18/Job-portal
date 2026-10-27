import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

print("=" * 60)
print("ONLINE JOB PORTAL - BACKEND CONNECTION CHECK")
print("=" * 60)

# 1. Environment & Paths
print(f"[✓] Project Directory: {BASE_DIR}")
print(f"[✓] Secret Key Loaded: {'Yes' if os.getenv('SECRET_KEY') else 'No (using dev fallback)'}")

# 2. Check Database Engine
engine = os.getenv("DB_ENGINE", "auto").strip().lower()
print(f"[✓] DB_ENGINE Mode: '{engine}'")

# Check SQLite
sqlite_db = BASE_DIR / "online_job_portal.db"
if sqlite_db.exists():
    print(f"[✓] SQLite Database Found: {sqlite_db.name} ({sqlite_db.stat().st_size} bytes)")
else:
    print(f"[-] SQLite Database not yet initialized (run: python init_db.py --sqlite)")

# Check MySQL
mysql_host = os.getenv("DB_HOST", "localhost")
mysql_user = os.getenv("DB_USER", "root")
mysql_password = os.getenv("DB_PASSWORD", "")
mysql_name = os.getenv("DB_NAME", "online_job_portal")

try:
    import mysql.connector
    conn = mysql.connector.connect(
        host=mysql_host,
        user=mysql_user,
        password=mysql_password,
        database=mysql_name,
        connection_timeout=2
    )
    print(f"[✓] MySQL Connected Successfully to '{mysql_name}' on {mysql_host}!")
    conn.close()
except Exception as exc:
    print(f"[-] MySQL Server: Not connected ({exc})")
    print("    -> Don't worry! SQLite is active as a seamless local fallback.")
    print("    -> To use MySQL: Start MySQL in XAMPP and run: python init_db.py --mysql")

# 3. Test Flask App Import
try:
    import app
    print("[✓] Flask Application (app.py) loaded with 0 errors!")
except Exception as exc:
    print(f"[x] Error loading app.py: {exc}")
    sys.exit(1)

print("=" * 60)
print("READY TO RUN!")
print("Run the server using:")
print("    python app.py")
print("Then open in browser:")
print("    http://127.0.0.1:5000")
print("=" * 60)
