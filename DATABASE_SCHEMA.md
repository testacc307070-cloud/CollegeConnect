# CollegeConnect — Database Schema

This is a concise description of the implemented MySQL schema. The executable source of truth is [`database/schema.sql`](database/schema.sql); the loader and tier classifier are in `scripts/`.

## Database and tables

The application uses the `collegeconnect` database with MySQL 8.x/InnoDB and `utf8mb4`.

| Table | Purpose | Key relationships |
|---|---|---|
| `colleges` | One row per institution, including name, district, type, and nullable institutional tier. | Primary key: `college_code`. |
| `branches` | One row per engineering branch/discipline. | Primary key: `branch_code`. |
| `historical_admissions` | Tall fact table containing a college/branch/year/community/quota cutoff and closing rank. | `college_code` and `branch_code` reference the dimension tables; unique slot key is `(college_code, branch_code, year, community, quota)`. |

### Historical admission fields

`historical_admissions` also contains a generated `record_id`, `is_partial`, and `created_at`. `cutoff_mark` and `closing_rank` are nullable: a missing/unallotted value is stored as `NULL`, not as zero. Community is constrained to `OC`, `BC`, `BCM`, `MBC`, `SC`, `SCA`, or `ST`. The bundled 2021–2025 source dataset and loader use `quota = 'GENERAL'`; other quota datasets are not bundled.

The fact table has composite indexes for community/quota/year cutoff and rank lookups, branch/year lookups, and year lookups. The college dimension has indexes on district, institution type, tier, and name; the branch dimension has a name index. These indexes support the query shapes used by the APIs; no fixed query-latency guarantee is made.

## Dataset and load process

`data/integrated/tnea_integrated_master.csv` contains 16,174 wide source offerings for 2021–2025. `scripts/load_database.py` unpivots seven community values per offering into 113,218 `historical_admissions` rows, preserves missing values as SQL `NULL`, and runs `scripts/classify_tiers.py` after loading. The current local system verification checks 467 colleges, 116 branches, and 113,218 admission rows; it reports tier counts of 69 Tier-1, 211 Tier-2, and 187 Tier-3.

To initialize a local copy, configure `.env`, start a compatible MySQL server, and run:

```powershell
python scripts\load_database.py
```

On Windows, [`start_mysql.bat`](start_mysql.bat) can initialize and start the local MySQL 8.4 data directory. That data directory is runtime state and is intentionally excluded from version control. Refer to [README.md](README.md) for complete setup and test steps.
