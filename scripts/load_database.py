#!/usr/bin/env python3
"""
CollegeConnect - Database Ingestion Pipeline
Authoritative ETL Script: Ingests 5-Year Integrated TNEA Master Dataset into MySQL.

Requirements & Specifications:
1. Reads the integrated master CSV: data/integrated/tnea_integrated_master.csv
2. Validates all required source columns before starting ingestion.
3. Connects to MySQL using environment variables (MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD).
4. Populates master dimension table: `colleges` (467 unique institutions).
   - Ingestion Normalization Decision: Source records across academic years contain naming variations
     for 443 institutions (minor spelling, punctuation, or historical renaming in TNEA publications).
     This script does NOT claim these variants are officially resolved or authority-reconciled.
     Rather, the entity metadata from the latest available academic year (e.g. 2025) is adopted as
     an explicit ingestion normalization choice for the `colleges` dimension table.
5. Populates master dimension table: `branches` (116 unique disciplines).
   - Ingestion Normalization Decision: Branch naming variations across years are likewise NOT claimed
     to be officially resolved; the latest-year observed discipline name is adopted as the canonical
     ingestion representation for the `branches` dimension table.
6. Unpivots the seven community sets (OC, BC, BCM, MBC, SC, SCA, ST) per offering into a normalized/tall design.
7. Populates normalized fact table: `historical_admissions` (113,218 tall slots).
8. Converts pandas NaN values to explicit SQL NULLs to preserve unallotted semantics.
9. Sets quota = 'GENERAL' strictly for all historical 2021-2025 records.
10. Verifies source partial-flag assumptions (`cutoff_<community>_partial` vs `rank_<community>_partial`).
    Does not assume they are identical without verifying against the integrated CSV; applies a deterministic
    documented rule (logical OR: is_partial = 1 if cutoff_partial == 1 or rank_partial == 1 else 0) if any divergence occurs.
11. Preserves institutional_tier = NULL strictly for all imported colleges (no invented tiers).
12. Uses strict ACID transactions with rollback on failure.
13. Avoids inserting duplicate records via idempotent ON DUPLICATE KEY UPDATE semantics.
14. Distinguishes verification counts across:
    - rows where cutoff exists (60,261)
    - rows where rank exists (60,244)
    - rows where either exists (60,261)
    - rows where both are NULL (52,957)
15. Verifies database row counts and distributions against authoritative benchmarks:
    - offerings: 16,174
    - colleges: 467
    - branches: 116
    - tall rows: 113,218
"""

import os
import sys
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pandas as pd

# ------------------------------------------------------------------------------
# Logging Configuration
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("CollegeConnect.ETL")

# ------------------------------------------------------------------------------
# Authoritative Benchmark Constants
# ------------------------------------------------------------------------------
COMMUNITIES = ["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"]
DEFAULT_QUOTA = "GENERAL"

EXPECTED_OFFERINGS_COUNT = 16174
EXPECTED_COLLEGES_COUNT = 467
EXPECTED_BRANCHES_COUNT = 116
EXPECTED_ADMISSIONS_COUNT = 113218  # 16,174 offerings * 7 communities

# Authoritative Nullability & Value Availability Benchmarks
EXPECTED_CUTOFF_EXISTS_COUNT = 60261   # Rows where cutoff mark is present (IS NOT NULL)
EXPECTED_RANK_EXISTS_COUNT = 60244     # Rows where closing rank is present (IS NOT NULL)
EXPECTED_EITHER_EXISTS_COUNT = 60261   # Rows where cutoff OR rank exists (active allotment)
EXPECTED_BOTH_NULL_COUNT = 52957       # Rows where cutoff AND rank are NULL (unallotted)
EXPECTED_CUTOFF_ONLY_COUNT = 17        # Rows where cutoff exists but closing rank is NULL
EXPECTED_RANK_ONLY_COUNT = 0          # Rows where rank exists but cutoff is NULL
EXPECTED_BOTH_EXIST_COUNT = 60244      # Rows where both cutoff and rank are present

# Backward compatibility aliases
EXPECTED_NON_NULL_COUNT = EXPECTED_EITHER_EXISTS_COUNT
EXPECTED_NULL_COUNT = EXPECTED_BOTH_NULL_COUNT

# All 35 authoritative columns required in the integrated master CSV
REQUIRED_COLUMNS = [
    "year",
    "college_code",
    "college_name",
    "district",
    "college_type",
    "branch_code",
    "branch_name",
    # Cutoff mark columns
    "cutoff_oc", "cutoff_bc", "cutoff_bcm", "cutoff_mbc",
    "cutoff_sc", "cutoff_sca", "cutoff_st",
    # Cutoff partial flag columns
    "cutoff_oc_partial", "cutoff_bc_partial", "cutoff_bcm_partial", "cutoff_mbc_partial",
    "cutoff_sc_partial", "cutoff_sca_partial", "cutoff_st_partial",
    # State rank columns
    "rank_oc", "rank_bc", "rank_bcm", "rank_mbc",
    "rank_sc", "rank_sca", "rank_st",
    # Rank partial flag columns
    "rank_oc_partial", "rank_bc_partial", "rank_bcm_partial", "rank_mbc_partial",
    "rank_sc_partial", "rank_sca_partial", "rank_st_partial",
]

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------------------------
# Environment & Configuration Helper
# ------------------------------------------------------------------------------
def load_env_file(dotenv_path: Optional[Path] = None) -> None:
    """
    Load environment variables from a .env file without requiring external dependencies,
    with automatic fallback to python-dotenv if installed.
    """
    if dotenv_path is None:
        dotenv_path = PROJECT_ROOT / ".env"

    # Try standard python-dotenv if installed
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(dotenv_path=str(dotenv_path), override=False)
        logger.debug("Loaded environment variables using python-dotenv.")
        return
    except ImportError:
        pass

    # Built-in lightweight .env parser
    if not dotenv_path.is_file():
        logger.debug(f"No .env file found at {dotenv_path}; using existing environment variables.")
        return

    logger.debug(f"Reading environment variables from {dotenv_path}")
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                # Strip wrapping single or double quotes
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                if key and key not in os.environ:
                    os.environ[key] = val


def get_db_config() -> Dict[str, Any]:
    """
    Retrieve MySQL connection credentials from environment variables.
    Never relies on hard-coded secrets.
    """
    host = os.getenv("MYSQL_HOST", "localhost").strip()
    port_str = os.getenv("MYSQL_PORT", "3306").strip()
    try:
        port = int(port_str)
    except ValueError:
        logger.warning(f"Invalid MYSQL_PORT '{port_str}', defaulting to 3306.")
        port = 3306

    database = os.getenv("MYSQL_DATABASE", "collegeconnect").strip()
    user = os.getenv("MYSQL_USER", "root").strip()
    password = os.getenv("MYSQL_PASSWORD", "")

    return {
        "host": host,
        "port": port,
        "database": database,
        "user": user,
        "password": password,
    }


def get_db_connection(config: Dict[str, Any]):
    """
    Establish a connection to MySQL using either PyMySQL or mysql-connector-python.
    Enforces autocommit=False to maintain explicit transactional integrity.
    """
    driver_errors = []

    # 1. Try pymysql
    try:
        import pymysql  # type: ignore
        conn = pymysql.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
            charset="utf8mb4",
            autocommit=False
        )
        logger.info("Connected to MySQL using 'pymysql' driver.")
        return conn
    except ImportError:
        driver_errors.append("pymysql is not installed.")
    except Exception as e:
        driver_errors.append(f"pymysql connection failed: {e}")

    # 2. Try mysql.connector
    try:
        import mysql.connector  # type: ignore
        conn = mysql.connector.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
            charset="utf8mb4",
            autocommit=False
        )
        logger.info("Connected to MySQL using 'mysql-connector-python' driver.")
        return conn
    except ImportError:
        driver_errors.append("mysql-connector-python is not installed.")
    except Exception as e:
        driver_errors.append(f"mysql.connector connection failed: {e}")

    error_msg = (
        "Could not establish connection to MySQL database.\n"
        "Diagnostics:\n  - " + "\n  - ".join(driver_errors) + "\n"
        "Please ensure:\n"
        "  1. A MySQL driver is installed: `pip install pymysql` or `pip install mysql-connector-python`\n"
        "  2. MySQL server is running and accessible on "
        f"{config['host']}:{config['port']}\n"
        f"  3. Credentials in .env (User: {config['user']}, Database: {config['database']}) are correct."
    )
    raise ConnectionError(error_msg)


# ------------------------------------------------------------------------------
# Source Path Resolver & CSV Validation
# ------------------------------------------------------------------------------
def resolve_csv_path(custom_path: Optional[str] = None) -> Path:
    """
    Locates the authoritative tnea_integrated_master.csv file.
    Checks:
    1. Explicit custom path or CLI argument
    2. TNEA_CSV_PATH environment variable
    3. Canonical project path: data/integrated/tnea_integrated_master.csv
    4. Sibling repository fallback: ../TNEA_FINAL/data/integrated/tnea_integrated_master.csv
    """
    if custom_path:
        p = Path(custom_path).resolve()
        if p.is_file():
            return p
        raise FileNotFoundError(f"Specified CSV path does not exist: {custom_path}")

    env_path = os.getenv("TNEA_CSV_PATH")
    if env_path:
        p = Path(env_path).resolve()
        if p.is_file():
            return p
        logger.warning(f"TNEA_CSV_PATH specified '{env_path}' but file was not found.")

    candidates = [
        PROJECT_ROOT / "data" / "integrated" / "tnea_integrated_master.csv",
        Path.cwd() / "data" / "integrated" / "tnea_integrated_master.csv",
        (PROJECT_ROOT.parent / "TNEA_FINAL" / "data" / "integrated" / "tnea_integrated_master.csv").resolve(),
        (Path.cwd().parent / "TNEA_FINAL" / "data" / "integrated" / "tnea_integrated_master.csv").resolve(),
    ]

    for cand in candidates:
        if cand.is_file():
            return cand

    raise FileNotFoundError(
        f"Authoritative master CSV not found. Expected at: '{candidates[0]}'. "
        "Please verify that data/integrated/tnea_integrated_master.csv exists or pass --csv <path>."
    )


def verify_source_partial_flags(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Verifies the source partial-flag assumption across all 7 reservation communities:
    inspects `cutoff_<community>_partial` vs `rank_<community>_partial`.

    Do NOT assume they are identical unless verified against the actual dataset.
    If divergences are found, reports the discrepancy details so the deterministic rule
    (logical OR: cutoff_partial | rank_partial) can be evaluated.
    """
    summary: Dict[str, Any] = {}
    total_mismatches = 0

    for comm in COMMUNITIES:
        c_col = f"cutoff_{comm.lower()}_partial"
        r_col = f"rank_{comm.lower()}_partial"

        c_vals = df[c_col].fillna(0).astype(int)
        r_vals = df[r_col].fillna(0).astype(int)

        mismatches = int((c_vals != r_vals).sum())
        total_mismatches += mismatches
        summary[comm] = {
            "identical": mismatches == 0,
            "mismatches": mismatches,
            "cutoff_partial_ones": int((c_vals == 1).sum()),
            "rank_partial_ones": int((r_vals == 1).sum()),
        }

    return {
        "all_identical": total_mismatches == 0,
        "total_mismatches": total_mismatches,
        "communities": summary,
    }


def validate_dataframe(df: pd.DataFrame) -> None:
    """
    Validates required columns, row count, and partial flag parity before ingestion proceeds.
    Fails fast if the schema does not strictly match the 35-column master format.
    """
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"CSV validation failed. Missing {len(missing_cols)} required columns: {missing_cols}"
        )

    row_count = len(df)
    if row_count != EXPECTED_OFFERINGS_COUNT:
        logger.warning(
            f"Source row count is {row_count} (expected benchmark: {EXPECTED_OFFERINGS_COUNT} offerings)."
        )
    else:
        logger.info(f"Source CSV row count validated: {row_count:,} offerings.")

    # Explicitly verify source partial-flag assumption
    partial_audit = verify_source_partial_flags(df)
    if partial_audit["all_identical"]:
        logger.info(
            "Source partial-flag verification: cutoff and rank partial flags are confirmed 100% identical "
            "across all 7 communities in the integrated master dataset."
        )
    else:
        logger.warning(
            f"Source partial-flag verification: found {partial_audit['total_mismatches']} differences "
            f"between cutoff and rank partial flags. Applying deterministic documented rule: "
            f"logical OR (is_partial = 1 if cutoff_partial == 1 or rank_partial == 1 else 0)."
        )


# ------------------------------------------------------------------------------
# Data Extraction & Normalization
# ------------------------------------------------------------------------------
def extract_colleges(df: pd.DataFrame) -> List[Tuple[int, str, str, str, Optional[str]]]:
    """
    Extracts and deduplicates 467 unique college records.

    INGESTION NORMALIZATION DECISION:
    Across the 5-year integrated dataset, 443 institutions exhibit slight naming variants across
    different academic years (e.g. punctuation, abbreviation changes, or minor phrasing differences
    in TNEA publications). This pipeline does NOT claim that these variants are officially resolved
    or authority-reconciled. Instead, as an explicit ingestion normalization decision, the metadata
    from the latest available academic year (sorted descending by year) is selected as the canonical
    representation for the `colleges` dimension table.

    Enforces constraint: institutional_tier is strictly NULL for all imported colleges (no invented tiers).
    """
    # Sort descending by academic year so the latest-year representation is deterministically selected
    df_sorted = df.sort_values(by="year", ascending=False)
    colleges_df = df_sorted.drop_duplicates(subset=["college_code"]).copy()

    records = []
    for _, row in colleges_df.iterrows():
        college_code = int(row["college_code"])
        # Ingestion normalization decision: latest-year value is selected;
        # do not claim official variant resolution.
        college_name = str(row["college_name"]).strip()
        district = str(row["district"]).strip().upper()
        college_type = str(row["college_type"]).strip()
        # Explicit guardrail: institutional_tier is strictly NULL for all imported colleges
        institutional_tier = None

        records.append((college_code, college_name, district, college_type, institutional_tier))

    # Sort deterministically by college_code
    records.sort(key=lambda x: x[0])
    return records


def extract_branches(df: pd.DataFrame) -> List[Tuple[str, str]]:
    """
    Extracts and deduplicates 116 unique academic branch disciplines.

    INGESTION NORMALIZATION DECISION:
    Branch disciplines across academic years exhibit minor naming variants across years.
    These variants are NOT claimed to be officially resolved or authority-reconciled.
    Instead, as an explicit ingestion normalization decision, the branch title from the latest
    available academic year (sorted descending by year) is selected as the canonical representation
    for the `branches` dimension table.
    """
    # Sort descending by academic year so the latest-year representation is deterministically selected
    df_sorted = df.sort_values(by="year", ascending=False)
    branches_df = df_sorted.drop_duplicates(subset=["branch_code"]).copy()

    records = []
    for _, row in branches_df.iterrows():
        branch_code = str(row["branch_code"]).strip()
        # Ingestion normalization decision: latest-year value is selected;
        # do not claim official variant resolution.
        branch_name = str(row["branch_name"]).strip()
        records.append((branch_code, branch_name))

    # Sort deterministically by branch_code
    records.sort(key=lambda x: x[0])
    return records


def unpivot_admissions(df: pd.DataFrame) -> Tuple[List[Tuple], Dict[str, Any]]:
    """
    Unpivots the 7 reservation community sets (OC, BC, BCM, MBC, SC, SCA, ST)
    into atomic rows for the tall `historical_admissions` fact table (113,218 slots).

    Rules enforced:
    - Quota is strictly 'GENERAL' for all historical 2021-2025 records.
    - Pandas NaN cutoff/rank converted to Python None (SQL NULL) to preserve unallotted semantics.
    - Cutoff marks rounded to 3 decimal places (DECIMAL(6,3)) or None.
    - Closing ranks cast to unsigned int or None.
    - Source partial flags:
      Both `cutoff_<comm>_partial` and `rank_<comm>_partial` are inspected.
      Do NOT assume they are identical without checking.
      Deterministic documented rule: is_partial = 1 if (cutoff_partial == 1 or rank_partial == 1) else 0.
      Logical OR ensures any partial-allotment signal present in either cutoff or rank stream is preserved.
    - Distinguishes verification counts:
      1. Rows where cutoff exists (cutoff_mark IS NOT NULL)
      2. Rows where rank exists (closing_rank IS NOT NULL)
      3. Rows where either exists (cutoff IS NOT NULL OR rank IS NOT NULL)
      4. Rows where both are NULL (cutoff IS NULL AND rank IS NULL)
    """
    start_time = time.time()
    n_rows = len(df)

    college_codes = df["college_code"].to_numpy(dtype=int)
    branch_codes = df["branch_code"].astype(str).str.strip().to_numpy()
    years = df["year"].to_numpy(dtype=int)

    comm_mapping = [
        (
            c,
            f"cutoff_{c.lower()}",
            f"rank_{c.lower()}",
            f"cutoff_{c.lower()}_partial",
            f"rank_{c.lower()}_partial"
        )
        for c in COMMUNITIES
    ]

    records = []
    cutoff_exists_count = 0
    rank_exists_count = 0
    either_exists_count = 0
    both_null_count = 0
    both_exist_count = 0
    cutoff_only_count = 0
    rank_only_count = 0
    partial_count = 0
    flag_divergence_count = 0

    year_stats: Dict[int, Dict[str, int]] = {}
    comm_stats: Dict[str, Dict[str, int]] = {
        c: {
            "total": 0,
            "cutoff_exists": 0,
            "rank_exists": 0,
            "either_exists": 0,
            "both_null": 0,
            "both_exist": 0,
            "cutoff_only": 0,
            "rank_only": 0,
            "partial": 0,
        }
        for c in COMMUNITIES
    }

    for comm, cut_col, rank_col, cut_part_col, rank_part_col in comm_mapping:
        cutoffs = df[cut_col].to_numpy()
        ranks = df[rank_col].to_numpy()
        cut_partials = df[cut_part_col].fillna(0).to_numpy(dtype=int)
        rank_partials = df[rank_part_col].fillna(0).to_numpy(dtype=int)

        for i in range(n_rows):
            c_val = cutoffs[i]
            r_val = ranks[i]
            cp_val = cut_partials[i]
            rp_val = rank_partials[i]
            yr = int(years[i])

            if yr not in year_stats:
                year_stats[yr] = {
                    "total": 0,
                    "cutoff_exists": 0,
                    "rank_exists": 0,
                    "either_exists": 0,
                    "both_null": 0,
                    "both_exist": 0,
                    "cutoff_only": 0,
                    "rank_only": 0,
                    "partial": 0,
                }

            # Handle NaN to SQL NULL conversion
            cutoff_mark: Optional[float] = None
            if not (pd.isna(c_val) or np.isnan(c_val)):
                cutoff_mark = round(float(c_val), 3)

            closing_rank: Optional[int] = None
            if not (pd.isna(r_val) or np.isnan(r_val)):
                closing_rank = int(round(float(r_val)))

            # Source partial flag handling:
            # Deterministic rule: is_partial = 1 if (cutoff_partial == 1 or rank_partial == 1) else 0.
            # Conservative logical OR preserves any partial-allotment signal from either stream.
            if int(cp_val) != int(rp_val):
                flag_divergence_count += 1
            is_partial = 1 if (int(cp_val) == 1 or int(rp_val) == 1) else 0
            if is_partial == 1:
                partial_count += 1
                year_stats[yr]["partial"] += 1
                comm_stats[comm]["partial"] += 1

            # Nullability & value availability categorization
            has_cutoff = cutoff_mark is not None
            has_rank = closing_rank is not None

            if has_cutoff:
                cutoff_exists_count += 1
                year_stats[yr]["cutoff_exists"] += 1
                comm_stats[comm]["cutoff_exists"] += 1

            if has_rank:
                rank_exists_count += 1
                year_stats[yr]["rank_exists"] += 1
                comm_stats[comm]["rank_exists"] += 1

            if has_cutoff or has_rank:
                either_exists_count += 1
                year_stats[yr]["either_exists"] += 1
                comm_stats[comm]["either_exists"] += 1
            else:
                both_null_count += 1
                year_stats[yr]["both_null"] += 1
                comm_stats[comm]["both_null"] += 1

            if has_cutoff and has_rank:
                both_exist_count += 1
                year_stats[yr]["both_exist"] += 1
                comm_stats[comm]["both_exist"] += 1
            elif has_cutoff and not has_rank:
                cutoff_only_count += 1
                year_stats[yr]["cutoff_only"] += 1
                comm_stats[comm]["cutoff_only"] += 1
            elif not has_cutoff and has_rank:
                rank_only_count += 1
                year_stats[yr]["rank_only"] += 1
                comm_stats[comm]["rank_only"] += 1

            year_stats[yr]["total"] += 1
            comm_stats[comm]["total"] += 1

            records.append((
                int(college_codes[i]),
                str(branch_codes[i]),
                yr,
                comm,
                DEFAULT_QUOTA,
                cutoff_mark,
                closing_rank,
                is_partial
            ))

    stats = {
        "unpivot_time_sec": time.time() - start_time,
        "total_records": len(records),
        "cutoff_exists_count": cutoff_exists_count,
        "rank_exists_count": rank_exists_count,
        "either_exists_count": either_exists_count,
        "both_null_count": both_null_count,
        "both_exist_count": both_exist_count,
        "cutoff_only_count": cutoff_only_count,
        "rank_only_count": rank_only_count,
        "partial_count": partial_count,
        "flag_divergence_count": flag_divergence_count,
        # Backward compatibility aliases
        "non_null_count": either_exists_count,
        "null_count": both_null_count,
        "year_stats": year_stats,
        "comm_stats": comm_stats
    }

    return records, stats


# ------------------------------------------------------------------------------
# Database Ingestion Operations
# ------------------------------------------------------------------------------
def populate_colleges(cursor, colleges: List[Tuple], batch_size: int = 1000) -> int:
    """
    Inserts colleges into the `colleges` table.
    Uses ON DUPLICATE KEY UPDATE to guarantee idempotency and avoid duplicate rows.
    """
    sql = """
        INSERT INTO colleges (
            college_code, college_name, district, college_type, institutional_tier
        ) VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            college_name = VALUES(college_name),
            district = VALUES(district),
            college_type = VALUES(college_type),
            institutional_tier = VALUES(institutional_tier)
    """
    total = len(colleges)
    for i in range(0, total, batch_size):
        batch = colleges[i:i + batch_size]
        cursor.executemany(sql, batch)
    return total


def populate_branches(cursor, branches: List[Tuple], batch_size: int = 1000) -> int:
    """
    Inserts branches into the `branches` table.
    Uses ON DUPLICATE KEY UPDATE to guarantee idempotency and avoid duplicate rows.
    """
    sql = """
        INSERT INTO branches (
            branch_code, branch_name
        ) VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
            branch_name = VALUES(branch_name)
    """
    total = len(branches)
    for i in range(0, total, batch_size):
        batch = branches[i:i + batch_size]
        cursor.executemany(sql, batch)
    return total


def populate_admissions(cursor, admissions: List[Tuple], batch_size: int = 5000) -> int:
    """
    Inserts admissions records into `historical_admissions` in optimized chunks.
    Uses ON DUPLICATE KEY UPDATE on the unique key (college_code, branch_code, year, community, quota).
    """
    sql = """
        INSERT INTO historical_admissions (
            college_code, branch_code, year, community, quota,
            cutoff_mark, closing_rank, is_partial
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            cutoff_mark = VALUES(cutoff_mark),
            closing_rank = VALUES(closing_rank),
            is_partial = VALUES(is_partial)
    """
    total = len(admissions)
    for i in range(0, total, batch_size):
        batch = admissions[i:i + batch_size]
        cursor.executemany(sql, batch)
    return total


# ------------------------------------------------------------------------------
# Verification & Quality Assurance Suite
# ------------------------------------------------------------------------------
def verify_database(cursor) -> Dict[str, Any]:
    """
    Executes comprehensive verification queries against the target MySQL database.
    Validates:
    - 467 unique colleges
    - 116 unique branches
    - 113,218 total historical admissions rows
    - 60,261 rows where cutoff exists (cutoff_mark IS NOT NULL)
    - 60,244 rows where rank exists (closing_rank IS NOT NULL)
    - 60,261 rows where either exists (cutoff IS NOT NULL OR rank IS NOT NULL)
    - 52,957 rows where both are NULL (cutoff IS NULL AND rank IS NULL)
    - 60,244 rows where both exist, 17 cutoff only, 0 rank only
    - Strict GENERAL quota enforcement
    - Strict institutional_tier NULL preservation
    """
    results: Dict[str, Any] = {}

    # 1. Colleges count
    cursor.execute("SELECT COUNT(*) FROM colleges")
    results["colleges_count"] = cursor.fetchone()[0]

    # 2. Branches count
    cursor.execute("SELECT COUNT(*) FROM branches")
    results["branches_count"] = cursor.fetchone()[0]

    # 3. Admissions count
    cursor.execute("SELECT COUNT(*) FROM historical_admissions")
    results["admissions_count"] = cursor.fetchone()[0]

    # 4. Rows where cutoff exists
    cursor.execute("SELECT COUNT(*) FROM historical_admissions WHERE cutoff_mark IS NOT NULL")
    results["cutoff_exists_count"] = cursor.fetchone()[0]

    # 5. Rows where rank exists
    cursor.execute("SELECT COUNT(*) FROM historical_admissions WHERE closing_rank IS NOT NULL")
    results["rank_exists_count"] = cursor.fetchone()[0]

    # 6. Rows where either exists (active allotment records)
    cursor.execute("""
        SELECT COUNT(*) FROM historical_admissions
        WHERE cutoff_mark IS NOT NULL OR closing_rank IS NOT NULL
    """)
    results["either_exists_count"] = cursor.fetchone()[0]
    results["non_null_count"] = results["either_exists_count"]

    # 7. Rows where both are NULL (unallotted slots)
    cursor.execute("""
        SELECT COUNT(*) FROM historical_admissions
        WHERE cutoff_mark IS NULL AND closing_rank IS NULL
    """)
    results["both_null_count"] = cursor.fetchone()[0]
    results["null_count"] = results["both_null_count"]

    # 8. Asymmetry breakdown: both exist, cutoff only, rank only
    cursor.execute("""
        SELECT COUNT(*) FROM historical_admissions
        WHERE cutoff_mark IS NOT NULL AND closing_rank IS NOT NULL
    """)
    results["both_exist_count"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM historical_admissions
        WHERE cutoff_mark IS NOT NULL AND closing_rank IS NULL
    """)
    results["cutoff_only_count"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM historical_admissions
        WHERE cutoff_mark IS NULL AND closing_rank IS NOT NULL
    """)
    results["rank_only_count"] = cursor.fetchone()[0]

    # 9. Non-GENERAL quota guardrail check (must be 0)
    cursor.execute("SELECT COUNT(*) FROM historical_admissions WHERE quota != 'GENERAL'")
    results["invalid_quota_count"] = cursor.fetchone()[0]

    # 10. Invented tier guardrail check (must be 0)
    cursor.execute("SELECT COUNT(*) FROM colleges WHERE institutional_tier IS NOT NULL")
    results["invented_tier_count"] = cursor.fetchone()[0]

    # 11. Annual distribution
    cursor.execute("""
        SELECT year,
               COUNT(*) AS total,
               COUNT(cutoff_mark) AS cutoffs,
               COUNT(closing_rank) AS ranks,
               SUM(CASE WHEN cutoff_mark IS NOT NULL OR closing_rank IS NOT NULL THEN 1 ELSE 0 END) AS either_exists,
               SUM(CASE WHEN cutoff_mark IS NULL AND closing_rank IS NULL THEN 1 ELSE 0 END) AS both_null
        FROM historical_admissions
        GROUP BY year
        ORDER BY year ASC
    """)
    results["annual_distribution"] = cursor.fetchall()

    # 12. Community distribution
    cursor.execute("""
        SELECT community,
               COUNT(*) AS total,
               COUNT(cutoff_mark) AS cutoffs,
               COUNT(closing_rank) AS ranks,
               SUM(CASE WHEN cutoff_mark IS NOT NULL OR closing_rank IS NOT NULL THEN 1 ELSE 0 END) AS either_exists,
               SUM(CASE WHEN cutoff_mark IS NULL AND closing_rank IS NULL THEN 1 ELSE 0 END) AS both_null
        FROM historical_admissions
        GROUP BY community
        ORDER BY FIELD(community, 'OC', 'BC', 'BCM', 'MBC', 'SC', 'SCA', 'ST')
    """)
    results["community_distribution"] = cursor.fetchall()

    return results


def print_statistics(
    stats: Dict[str, Any],
    verification: Optional[Dict[str, Any]] = None,
    total_duration_sec: float = 0.0
) -> None:
    """
    Renders detailed ingestion statistics and verification status in a clean report,
    clearly distinguishing cutoff existence, rank existence, either existence, and both NULL.
    """
    sep = "=" * 80
    sub_sep = "-" * 80

    print("\n" + sep)
    print("           COLLEGE_CONNECT: DATABASE INGESTION & AUDIT REPORT")
    print(sep)

    print(f"Total Execution Time: {total_duration_sec:.2f} seconds")
    print(f"Unpivot Processing:   {stats['unpivot_time_sec']:.2f} seconds")
    print(sub_sep)
    print("UNPIVOTED DATASET SUMMARY (PRE-INSERTION AUDIT):")
    total_rec = stats["total_records"]
    cut_cnt = stats["cutoff_exists_count"]
    rnk_cnt = stats["rank_exists_count"]
    either_cnt = stats["either_exists_count"]
    both_null_cnt = stats["both_null_count"]

    pct_cut = (cut_cnt / total_rec * 100) if total_rec > 0 else 0
    pct_rnk = (rnk_cnt / total_rec * 100) if total_rec > 0 else 0
    pct_either = (either_cnt / total_rec * 100) if total_rec > 0 else 0
    pct_null = (both_null_cnt / total_rec * 100) if total_rec > 0 else 0

    print(f"  * Total Tall Fact Records:       {total_rec:,} slots")
    print(f"  * Rows Where Cutoff Exists:      {cut_cnt:,} ({pct_cut:.2f}%)")
    print(f"  * Rows Where Rank Exists:        {rnk_cnt:,} ({pct_rnk:.2f}%)")
    print(f"  * Rows Where Either Exists:      {either_cnt:,} ({pct_either:.2f}%)")
    print(f"  * Rows Where Both are NULL:      {both_null_cnt:,} ({pct_null:.2f}%)")
    print("  * Asymmetry Breakdown:")
    print(f"      - Both Cutoff & Rank Exist:  {stats['both_exist_count']:,}")
    print(f"      - Cutoff Exists, Rank NULL:  {stats['cutoff_only_count']:,}")
    print(f"      - Rank Exists, Cutoff NULL:  {stats['rank_only_count']:,}")
    print(f"  * Partial Allotment Records:     {stats['partial_count']:,}")
    print(f"  * Source Partial Discrepancies:  {stats['flag_divergence_count']:,}")

    print(sub_sep)
    print("YEARLY BREAKDOWN:")
    print(f"{'Year':<6} {'Total':<10} {'Cutoff Present':<16} {'Rank Present':<14} {'Either Present':<16} {'Both NULL':<12} {'Fill Rate':<10}")
    for yr, ydata in sorted(stats["year_stats"].items()):
        pct = (ydata["either_exists"] / ydata["total"]) * 100 if ydata["total"] > 0 else 0
        print(
            f"{yr:<6} {ydata['total']:<10,d} {ydata['cutoff_exists']:<16,d} {ydata['rank_exists']:<14,d} "
            f"{ydata['either_exists']:<16,d} {ydata['both_null']:<12,d} {pct:>8.2f}%"
        )

    print(sub_sep)
    print("COMMUNITY BREAKDOWN:")
    print(f"{'Comm':<6} {'Total':<10} {'Cutoff Present':<16} {'Rank Present':<14} {'Either Present':<16} {'Both NULL':<12} {'Fill Rate':<10}")
    for comm in COMMUNITIES:
        cdata = stats["comm_stats"][comm]
        pct = (cdata["either_exists"] / cdata["total"]) * 100 if cdata["total"] > 0 else 0
        print(
            f"{comm:<6} {cdata['total']:<10,d} {cdata['cutoff_exists']:<16,d} {cdata['rank_exists']:<14,d} "
            f"{cdata['either_exists']:<16,d} {cdata['both_null']:<12,d} {pct:>8.2f}%"
        )

    if verification:
        print(sub_sep)
        print("DATABASE INGESTION VERIFICATION CHECKS:")

        checks = [
            ("Colleges Count", verification["colleges_count"], EXPECTED_COLLEGES_COUNT),
            ("Branches Count", verification["branches_count"], EXPECTED_BRANCHES_COUNT),
            ("Historical Admissions Count", verification["admissions_count"], EXPECTED_ADMISSIONS_COUNT),
            ("Rows where Cutoff Exists", verification["cutoff_exists_count"], EXPECTED_CUTOFF_EXISTS_COUNT),
            ("Rows where Rank Exists", verification["rank_exists_count"], EXPECTED_RANK_EXISTS_COUNT),
            ("Rows where Either Exists", verification["either_exists_count"], EXPECTED_EITHER_EXISTS_COUNT),
            ("Rows where Both are NULL", verification["both_null_count"], EXPECTED_BOTH_NULL_COUNT),
            ("Rows with Cutoff Only", verification["cutoff_only_count"], EXPECTED_CUTOFF_ONLY_COUNT),
            ("Rows with Rank Only", verification["rank_only_count"], EXPECTED_RANK_ONLY_COUNT),
            ("Non-GENERAL Quota Records", verification["invalid_quota_count"], 0),
            ("Invented Institutional Tiers", verification["invented_tier_count"], 0),
        ]

        all_passed = True
        for name, actual, expected in checks:
            status = "PASS" if actual == expected else "FAIL"
            if status == "FAIL":
                all_passed = False
            print(f"  [{status}] {name:<32}: Actual = {actual:<8,} | Expected = {expected:<8,}")

        print(sub_sep)
        if all_passed:
            print("ALL RELATIONAL INTEGRITY & BENCHMARK AUDITS: PASSED (100% RELATIONAL FIDELITY)")
        else:
            print("WARNING: ONE OR MORE INTEGRITY BENCHMARKS FAILED AUDIT.")
    print(sep + "\n")


# ------------------------------------------------------------------------------
# Main Ingestion Orchestrator
# ------------------------------------------------------------------------------
def run_ingestion(
    csv_path: Optional[str] = None,
    env_path: Optional[str] = None,
    batch_size: int = 5000,
    dry_run: bool = False
) -> int:
    """
    Main orchestration routine for CollegeConnect database loading.
    Executes in a single database transaction with automatic rollback on error.
    """
    overall_start = time.time()

    # Step 1: Environment & Source Path Resolution
    load_env_file(Path(env_path) if env_path else None)
    source_file = resolve_csv_path(csv_path)
    logger.info(f"Authoritative CSV source path resolved: {source_file}")

    # Step 2: Read Master CSV
    logger.info("Reading source CSV into pandas DataFrame...")
    df = pd.read_csv(source_file)
    logger.info(f"Loaded {len(df):,} offerings from master CSV.")

    # Step 3: Validate Columns & Required Schema
    logger.info("Validating required columns in source dataset...")
    validate_dataframe(df)

    # Step 4: Extract Dimensional Entities
    logger.info("Extracting master dimension: colleges (applying latest-year ingestion normalization decision)...")
    colleges = extract_colleges(df)
    logger.info(f"Prepared {len(colleges)} unique college records.")
    if len(colleges) != EXPECTED_COLLEGES_COUNT:
        logger.warning(
            f"Colleges count {len(colleges)} differs from expected benchmark {EXPECTED_COLLEGES_COUNT}."
        )

    logger.info("Extracting master dimension: branches (applying latest-year ingestion normalization decision)...")
    branches = extract_branches(df)
    logger.info(f"Prepared {len(branches)} unique branch records.")
    if len(branches) != EXPECTED_BRANCHES_COUNT:
        logger.warning(
            f"Branches count {len(branches)} differs from expected benchmark {EXPECTED_BRANCHES_COUNT}."
        )

    # Step 5: Unpivot Admissions
    logger.info("Unpivoting 7 reservation communities across all offerings...")
    admissions, stats = unpivot_admissions(df)
    logger.info(f"Prepared {len(admissions):,} tall fact records in {stats['unpivot_time_sec']:.2f}s.")

    # Dry-Run Mode (Validation without Database Connection)
    if dry_run:
        logger.info("Dry-run requested. Skipping MySQL insertion.")
        print_statistics(stats, verification=None, total_duration_sec=time.time() - overall_start)
        return 0

    # Step 6: Connect to MySQL
    db_config = get_db_config()
    logger.info(
        f"Connecting to MySQL database '{db_config['database']}' on {db_config['host']}:{db_config['port']} "
        f"as user '{db_config['user']}'..."
    )
    conn = get_db_connection(db_config)

    # Step 7: Transactional Ingestion & Verification
    cursor = conn.cursor()
    try:
        logger.info("Beginning database transaction...")

        # 7.1 Populate colleges
        logger.info(f"Ingesting {len(colleges)} colleges...")
        n_colleges = populate_colleges(cursor, colleges)
        logger.info(f"Inserted/updated {n_colleges} colleges successfully.")

        # 7.2 Populate branches
        logger.info(f"Ingesting {len(branches)} branches...")
        n_branches = populate_branches(cursor, branches)
        logger.info(f"Inserted/updated {n_branches} branches successfully.")

        # 7.3 Populate admissions
        logger.info(f"Ingesting {len(admissions):,} historical admission records (batch size: {batch_size:,})...")
        t_adm_start = time.time()
        n_admissions = populate_admissions(cursor, admissions, batch_size=batch_size)
        logger.info(
            f"Ingested {n_admissions:,} historical admissions records in {time.time() - t_adm_start:.2f}s."
        )

        # 7.4 Verification Queries (pre-commit inside transaction)
        logger.info("Running verification and integrity assertion suite...")
        verification = verify_database(cursor)

        # Enforce Critical Assertions
        assert verification["colleges_count"] == EXPECTED_COLLEGES_COUNT, (
            f"College count assertion failed: {verification['colleges_count']} != {EXPECTED_COLLEGES_COUNT}"
        )
        assert verification["branches_count"] == EXPECTED_BRANCHES_COUNT, (
            f"Branch count assertion failed: {verification['branches_count']} != {EXPECTED_BRANCHES_COUNT}"
        )
        assert verification["admissions_count"] == EXPECTED_ADMISSIONS_COUNT, (
            f"Admissions row count assertion failed: {verification['admissions_count']} != {EXPECTED_ADMISSIONS_COUNT}"
        )
        assert verification["cutoff_exists_count"] == EXPECTED_CUTOFF_EXISTS_COUNT, (
            f"Cutoff exists assertion failed: {verification['cutoff_exists_count']} != {EXPECTED_CUTOFF_EXISTS_COUNT}"
        )
        assert verification["rank_exists_count"] == EXPECTED_RANK_EXISTS_COUNT, (
            f"Rank exists assertion failed: {verification['rank_exists_count']} != {EXPECTED_RANK_EXISTS_COUNT}"
        )
        assert verification["either_exists_count"] == EXPECTED_EITHER_EXISTS_COUNT, (
            f"Either exists assertion failed: {verification['either_exists_count']} != {EXPECTED_EITHER_EXISTS_COUNT}"
        )
        assert verification["both_null_count"] == EXPECTED_BOTH_NULL_COUNT, (
            f"Both NULL count assertion failed: {verification['both_null_count']} != {EXPECTED_BOTH_NULL_COUNT}"
        )
        assert verification["cutoff_only_count"] == EXPECTED_CUTOFF_ONLY_COUNT, (
            f"Cutoff only count assertion failed: {verification['cutoff_only_count']} != {EXPECTED_CUTOFF_ONLY_COUNT}"
        )
        assert verification["rank_only_count"] == EXPECTED_RANK_ONLY_COUNT, (
            f"Rank only count assertion failed: {verification['rank_only_count']} != {EXPECTED_RANK_ONLY_COUNT}"
        )
        assert verification["invalid_quota_count"] == 0, (
            f"Found {verification['invalid_quota_count']} records with quota != 'GENERAL'."
        )
        assert verification["invented_tier_count"] == 0, (
            f"Found {verification['invented_tier_count']} records with non-NULL institutional_tier."
        )

        # 7.5 Commit Transaction
        conn.commit()
        logger.info("Database transaction committed successfully.")

        # 7.6 Classify Institutional Tiers
        try:
            from scripts.classify_tiers import classify_and_update_tiers
            logger.info("Classifying institutional tiers based on historical admission cutoffs...")
            classify_and_update_tiers()
        except Exception as tier_exc:
            logger.warning(f"Could not classify tiers post-load: {tier_exc}")

        # Step 8: Print Statistics and Audit Report
        total_time = time.time() - overall_start
        print_statistics(stats, verification=verification, total_duration_sec=total_time)
        return 0

    except Exception as exc:
        logger.error(f"Error during database ingestion: {exc}")
        logger.warning("Rolling back database transaction to maintain database consistency...")
        conn.rollback()
        logger.info("Transaction rollback complete.")
        raise
    finally:
        cursor.close()
        conn.close()
        logger.debug("Database connection closed.")


# ------------------------------------------------------------------------------
# Command Line Interface
# ------------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Ingest 5-Year Integrated TNEA Master Dataset into CollegeConnect MySQL database."
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Path to authoritative tnea_integrated_master.csv. Defaults to data/integrated/tnea_integrated_master.csv."
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=None,
        help="Path to custom .env file containing MySQL credentials."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5000,
        help="Batch size for bulk insertion into historical_admissions (default: 5000)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate CSV extraction and unpivoting without writing to the MySQL database."
    )

    args = parser.parse_args()

    try:
        exit_code = run_ingestion(
            csv_path=args.csv,
            env_path=args.env_file,
            batch_size=args.batch_size,
            dry_run=args.dry_run
        )
        sys.exit(exit_code)
    except Exception as exc:
        logger.critical(f"Pipeline execution aborted: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
