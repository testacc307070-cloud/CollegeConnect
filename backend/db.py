"""Database connection helper for CollegeConnect with automatic recovery."""

import logging
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
import pymysql
from dotenv import load_dotenv

logger = logging.getLogger("collegeconnect.db")

# Load configuration from .env in the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _is_port_in_use(host: str, port: int) -> bool:
    """Test if a given TCP host and port are accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=1.5):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def ensure_mysql_running() -> bool:
    """
    Ensure the local MySQL database daemon is running.
    If unreachable on localhost, attempts to spawn the local mysqld process.
    """
    host = os.getenv("MYSQL_HOST", "localhost")
    port = int(os.getenv("MYSQL_PORT", 3306))

    if _is_port_in_use(host, port):
        return True

    if host.lower() not in ("localhost", "127.0.0.1"):
        return False

    candidates = [
        Path(r"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqld.exe"),
        Path(r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe"),
    ]
    mysqld_path = None
    for cand in candidates:
        if cand.is_file():
            mysqld_path = cand
            break

    if not mysqld_path:
        which_path = shutil.which("mysqld")
        if which_path:
            mysqld_path = Path(which_path)

    datadir = PROJECT_ROOT / "data" / "mysql_data"

    if mysqld_path and datadir.is_dir():
        logger.info(f"Attempting auto-start of MySQL daemon: {mysqld_path}")
        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | getattr(subprocess, "DETACHED_PROCESS", 0x00000008)

        cmd = [
            str(mysqld_path),
            f"--datadir={datadir.resolve()}",
            f"--port={port}",
            "--console"
        ]

        try:
            subprocess.Popen(
                cmd,
                cwd=str(PROJECT_ROOT),
                creationflags=creationflags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            for _ in range(20):
                time.sleep(0.5)
                if _is_port_in_use(host, port):
                    logger.info("MySQL daemon auto-started successfully.")
                    return True
        except Exception as e:
            logger.warning(f"Could not auto-start MySQL daemon: {e}")

    return False


def get_db_connection():
    """
    Establish and return a MySQL connection using PyMySQL.
    Configuration parameters are read from environment variables (.env).
    Automatically attempts self-recovery if local server is not running.
    """
    host = os.getenv("MYSQL_HOST", "localhost")
    port = int(os.getenv("MYSQL_PORT", 3306))
    database = os.getenv("MYSQL_DATABASE", "collegeconnect")
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "")

    def _connect():
        return pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset="utf8mb4"
        )

    try:
        return _connect()
    except pymysql.MySQLError as err:
        # Error 2003: Can't connect to MySQL server
        if err.args and err.args[0] == 2003:
            logger.warning("MySQL connection refused. Attempting self-healing daemon start...")
            if ensure_mysql_running():
                return _connect()
        raise


def safe_close(conn):
    """Safely close a MySQL connection if open."""
    if conn:
        try:
            conn.close()
        except Exception:
            pass
