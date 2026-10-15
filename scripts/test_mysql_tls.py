"""Focused tests for verified TLS configuration on remote MySQL connections."""

import os
import sys
import tempfile
import unittest
from importlib import import_module
from pathlib import Path
from unittest.mock import patch

# Prevent test imports from loading the user's real .env file.
os.environ["PYTHON_DOTENV_DISABLED"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.mysql_tls import mysql_tls_options
from scripts.load_database import get_db_connection, get_db_config

get_app_db_connection = import_module("backend.db").get_db_connection


class MySQLTlsTests(unittest.TestCase):
    def test_localhost_does_not_require_tls_configuration(self):
        self.assertEqual(mysql_tls_options("localhost", None), {})
        self.assertEqual(mysql_tls_options("127.0.0.1", ""), {})
        self.assertEqual(mysql_tls_options("::1", None), {})

    def test_remote_host_requires_ca_certificate(self):
        with self.assertRaisesRegex(ValueError, "MYSQL_SSL_CA"):
            mysql_tls_options("mysql.example.com", None)

    def test_ca_certificate_enables_full_verification(self):
        with tempfile.NamedTemporaryFile() as ca_file:
            self.assertEqual(
                mysql_tls_options("mysql.example.com", ca_file.name),
                {
                    "ssl_ca": ca_file.name,
                    "ssl_verify_cert": True,
                    "ssl_verify_identity": True,
                },
            )

    def test_missing_ca_file_is_rejected(self):
        with self.assertRaisesRegex(FileNotFoundError, "MYSQL_SSL_CA"):
            mysql_tls_options("localhost", "missing-ca.pem")

    def test_loader_reads_mysql_ssl_ca(self):
        settings = {
            "MYSQL_HOST": "localhost",
            "MYSQL_PORT": "3306",
            "MYSQL_DATABASE": "collegeconnect",
            "MYSQL_USER": "root",
            "MYSQL_PASSWORD": "",
            "MYSQL_SSL_CA": "",
        }
        with patch.dict(os.environ, settings, clear=False):
            self.assertEqual(get_db_config()["ssl_ca"], "")

    def test_loader_passes_verified_tls_options_to_pymysql(self):
        with tempfile.NamedTemporaryFile() as ca_file:
            config = {
                "host": "mysql.example.com",
                "port": 3306,
                "database": "collegeconnect",
                "user": "app",
                "password": "not-a-real-secret",
                "ssl_ca": ca_file.name,
            }
            with patch("pymysql.connect", return_value=object()) as connect:
                get_db_connection(config)

            self.assertEqual(connect.call_args.kwargs["ssl_ca"], ca_file.name)
            self.assertTrue(connect.call_args.kwargs["ssl_verify_cert"])
            self.assertTrue(connect.call_args.kwargs["ssl_verify_identity"])

    def test_app_passes_verified_tls_options_to_pymysql(self):
        with tempfile.NamedTemporaryFile() as ca_file:
            environment = {
                "MYSQL_HOST": "mysql.example.com",
                "MYSQL_PORT": "3306",
                "MYSQL_DATABASE": "collegeconnect",
                "MYSQL_USER": "app",
                "MYSQL_PASSWORD": "not-a-real-secret",
                "MYSQL_SSL_CA": ca_file.name,
            }
            with patch.dict(os.environ, environment, clear=False):
                with patch("pymysql.connect", return_value=object()) as connect:
                    get_app_db_connection()

            self.assertEqual(connect.call_args.kwargs["ssl_ca"], ca_file.name)
            self.assertTrue(connect.call_args.kwargs["ssl_verify_cert"])
            self.assertTrue(connect.call_args.kwargs["ssl_verify_identity"])


if __name__ == "__main__":
    unittest.main()
