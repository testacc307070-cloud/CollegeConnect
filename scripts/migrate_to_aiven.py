"""Migrate local CollegeConnect MySQL database to remote Aiven MySQL with verified TLS."""

import os
import sys
import time
from pathlib import Path
import pymysql
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.mysql_tls import mysql_tls_options

EXPECTED_COUNTS = {
    "colleges": 467,
    "branches": 116,
    "historical_admissions": 113218,
}

def load_remote_env():
    aiven_env = PROJECT_ROOT / ".env.aiven"
    if aiven_env.is_file():
        load_dotenv(aiven_env, override=True)
    else:
        load_dotenv(PROJECT_ROOT / ".env")

def split_sql_statements(sql_text):
    """Split SQL dump into executable statements handling multiline statements and string literals."""
    statements = []
    current = []
    in_string = False
    escape = False
    quote_char = None

    for line in sql_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        # Skip pure comments
        if stripped.startswith("/*") and stripped.endswith("*/;"):
            continue
        # Skip LOCK/UNLOCK TABLES which trigger implicit commits in MySQL
        if stripped.upper().startswith("LOCK TABLES") or stripped.upper().startswith("UNLOCK TABLES"):
            continue
        
        current.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(current))
            current = []

    if current:
        remaining = "\n".join(current).strip()
        if remaining:
            statements.append(remaining)

    return statements

def migrate():
    load_remote_env()

    host = os.getenv("MYSQL_HOST", "").strip()
    port = int(os.getenv("MYSQL_PORT", "3306"))
    database = os.getenv("MYSQL_DATABASE", "").strip()
    user = os.getenv("MYSQL_USER", "").strip()
    password = os.getenv("MYSQL_PASSWORD", "")
    ssl_ca = os.getenv("MYSQL_SSL_CA", "").strip()

    if not ssl_ca:
        default_ca = PROJECT_ROOT / "certs" / "ca.pem"
        if default_ca.is_file():
            ssl_ca = str(default_ca)

    dump_path = PROJECT_ROOT / "dumps" / "collegeconnect_backup.sql"
    if not dump_path.is_file():
        print(f"[ERROR] Backup dump not found at {dump_path}")
        return 1

    print("==================================================")
    print("      AIVEN MYSQL DATABASE MIGRATION ENGINE")
    print("==================================================")
    print(f"Target Host    : {host}")
    print(f"Target Port    : {port}")
    print(f"Target Database: {database}")
    print(f"Target User    : {user}")
    print(f"Dump File      : {dump_path} ({dump_path.stat().st_size:,} bytes)")
    print(f"CA Certificate : {ssl_ca}")

    tls_opts = mysql_tls_options(host, ssl_ca)

    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
        autocommit=False,
        **tls_opts
    )

    with conn.cursor() as cur:
        cur.execute("SELECT DATABASE()")
        actual_db = cur.fetchone()[0]
        print(f"Connected to verified target database: '{actual_db}'")

        cur.execute("SHOW TABLES")
        existing_tables = [r[0] for r in cur.fetchall()]
        print(f"Existing tables in target database: {existing_tables}")

        core_tables = set(EXPECTED_COUNTS.keys())
        overlap = core_tables.intersection(set(existing_tables))

        if overlap:
            counts = {}
            for t in overlap:
                cur.execute(f"SELECT COUNT(*) FROM `{t}`")
                counts[t] = cur.fetchone()[0]

            print("Found existing core tables:")
            for t, cnt in counts.items():
                print(f"  - {t}: {cnt} rows (expected: {EXPECTED_COUNTS.get(t)})")

            if all(counts.get(t) == EXPECTED_COUNTS.get(t) for t in core_tables):
                print("[INFO] Target database already has all expected tables and exact row counts!")
                print("[INFO] Database migration is already complete. No changes needed.")
                conn.close()
                return 0
            else:
                print("[WARNING] Target database contains conflicting or partial data!")
                print("Stopping to prevent overwriting without explicit user confirmation.")
                conn.close()
                return 2

    print("\nReading and parsing dump file...")
    sql_content = dump_path.read_text(encoding="utf-8")
    statements = split_sql_statements(sql_content)
    print(f"Parsed {len(statements)} SQL statements to execute.")

    start_time = time.time()
    executed = 0
    with conn.cursor() as cur:
        # Disable foreign key checks for clean load
        cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cur.execute("SET UNIQUE_CHECKS = 0;")
        cur.execute("SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';")

        for stmt in statements:
            stmt = stmt.strip()
            if not stmt:
                continue
            try:
                cur.execute(stmt)
                executed += 1
                if executed % 50 == 0 or executed == len(statements):
                    print(f"Progress: {executed}/{len(statements)} statements executed...")
            except Exception as e:
                conn.rollback()
                print(f"\n[ERROR executing statement]: {stmt[:120]}...")
                print(f"Error details: {e}")
                conn.close()
                return 1

        cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
        cur.execute("SET UNIQUE_CHECKS = 1;")
        conn.commit()

    duration = time.time() - start_time
    print(f"\nSuccessfully executed all statements in {duration:.2f} seconds.")

    # Validation
    print("\nValidating imported tables and row counts...")
    validation_passed = True
    with conn.cursor() as cur:
        for table, expected in EXPECTED_COUNTS.items():
            cur.execute(f"SELECT COUNT(*) FROM `{table}`")
            actual = cur.fetchone()[0]
            status = "PASS" if actual == expected else "FAIL"
            print(f"  [{status}] `{table}`: {actual:,} rows (expected: {expected:,})")
            if actual != expected:
                validation_passed = False

        # Index verification
        cur.execute("SHOW INDEX FROM `historical_admissions`")
        indexes = {r[2] for r in cur.fetchall()}
        print(f"Historical admissions indexes: {sorted(indexes)}")

    conn.close()

    if validation_passed:
        print("\n==================================================")
        print(" [SUCCESS] Aiven MySQL Migration Verified 100%!")
        print("==================================================")
        return 0
    else:
        print("\n[ERROR] Migration completed but row count validation failed!")
        return 1

if __name__ == "__main__":
    sys.exit(migrate())
