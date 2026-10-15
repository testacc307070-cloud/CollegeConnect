"""TLS configuration shared by the application and database loader."""

from pathlib import Path
from typing import Any, Dict, Optional


LOCAL_MYSQL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def mysql_tls_options(host: str, ca_file: Optional[str]) -> Dict[str, Any]:
    """Return verified TLS options, requiring a CA certificate for remote MySQL."""
    ca_path = (ca_file or "").strip()
    if not ca_path:
        if host.strip().lower() in LOCAL_MYSQL_HOSTS:
            return {}
        raise ValueError(
            "MYSQL_SSL_CA must reference the downloaded CA certificate for remote MySQL connections."
        )

    certificate = Path(ca_path).expanduser()
    if not certificate.is_file():
        raise FileNotFoundError(
            "MYSQL_SSL_CA must reference an existing CA certificate file."
        )

    return {
        "ssl_ca": str(certificate),
        "ssl_verify_cert": True,
        "ssl_verify_identity": True,
    }
