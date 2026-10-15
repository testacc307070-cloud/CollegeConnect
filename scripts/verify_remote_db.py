"""Safely verify remote MySQL connectivity (Aiven) with full TLS verification."""

import os
import sys
from pathlib import Path
import pymysql
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.mysql_tls import mysql_tls_options

def load_remote_env():
    aiven_env = PROJECT_ROOT / ".env.aiven"
    if aiven_env.is_file():
        load_dotenv(aiven_env, override=True)
    else:
        load_dotenv(PROJECT_ROOT / ".env")

def main():
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

    print("==================================================")
    print("      REMOTE MYSQL TLS CONNECTIVITY CHECK")
    print("==================================================")
    print(f"Target Host    : {host or '[NOT CONFIGURED]'}")
    print(f"Target Port    : {port}")
    print(f"Target Database: {database or '[NOT CONFIGURED]'}")
    print(f"Target User    : {user or '[NOT CONFIGURED]'}")
    print(f"Password Set   : {'YES' if password else 'NO'}")
    print(f"CA Certificate : {ssl_ca or '[MISSING]'}")
    print("--------------------------------------------------")

    if not host or not user or not password:
        print("[ERROR] Remote MySQL host, user, or password is not configured.")
        print("Please configure them in .env.aiven or your environment.")
        return 1

    try:
        tls_opts = mysql_tls_options(host, ssl_ca)
        print(f"TLS Verification: ENABLED (CA: {tls_opts.get('ssl_ca')})")
        print(f"Verify Cert     : {tls_opts.get('ssl_verify_cert')}")
        print(f"Verify Identity : {tls_opts.get('ssl_verify_identity')}")
    except Exception as e:
        print(f"[TLS CONFIG ERROR] {e}")
        return 1

    try:
        print("Connecting to remote MySQL server...")
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset="utf8mb4",
            **tls_opts
        )
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION()")
            version = cur.fetchone()[0]
            cur.execute("SELECT CURRENT_USER()")
            current_user = cur.fetchone()[0]
            cur.execute("SELECT DATABASE()")
            current_db = cur.fetchone()[0]

            print("[SUCCESS] Connected successfully via verified TLS!")
            print(f"MySQL Version : {version}")
            print(f"Current User  : {current_user}")
            print(f"Connected DB  : {current_db}")

            cur.execute("SHOW TABLES")
            tables = [r[0] for r in cur.fetchall()]
            print(f"Existing Tables in '{current_db}': {len(tables)}")
            if tables:
                print("Table list:")
                for t in tables:
                    cur.execute(f"SELECT COUNT(*) FROM `{t}`")
                    cnt = cur.fetchone()[0]
                    print(f"  - {t}: {cnt} rows")
            else:
                print("  Database is currently EMPTY and ready for migration.")

            # Privileges check
            try:
                cur.execute("SHOW GRANTS")
                grants = [r[0] for r in cur.fetchall()]
                print("\nUser Privileges:")
                for g in grants:
                    print(f"  {g}")
            except Exception as ge:
                print(f"Could not retrieve grants: {ge}")

            # Database storage allocation/usage
            try:
                cur.execute(
                    "SELECT COALESCE(SUM(data_length + index_length), 0) FROM information_schema.tables WHERE table_schema = %s",
                    (current_db,)
                )
                db_bytes = cur.fetchone()[0]
                print(f"Current DB Storage Used: {db_bytes:,} bytes ({db_bytes / (1024*1024):.2f} MB)")
            except Exception as se:
                print(f"Could not check storage usage: {se}")

        conn.close()
        print("==================================================")
        return 0
    except Exception as err:
        print(f"[CONNECTION FAILED] {err}")
        print("==================================================")
        return 1

if __name__ == "__main__":
    sys.exit(main())
