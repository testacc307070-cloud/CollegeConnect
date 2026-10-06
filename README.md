# CollegeConnect – TNEA Engineering College Admissions & Decision Support Platform

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask 3.1](https://img.shields.io/badge/Flask-3.1-black.svg)](https://flask.palletsprojects.com/)
[![MySQL 8.4](https://img.shields.io/badge/MySQL-8.4-orange.svg)](https://www.mysql.com/)
[![Google GenAI](https://img.shields.io/badge/Google_GenAI-Gemini_2.5_Flash-4285F4.svg)](https://ai.google.dev/)
[![Verification](https://img.shields.io/badge/Verification-26%2F26%20Passed%20(100%25)-success.svg)](scripts/verify_system.py)

CollegeConnect is an end-to-end, AI-assisted engineering college admissions counseling and decision support platform for **Tamil Nadu Engineering Admissions (TNEA)**. It models 5 years of verified historical admissions data (2021–2025) across 467 institutions and 116 engineering disciplines with deterministic statistical scoring, Google Gemini-powered Retrieval-Augmented Generation (RAG), Class 12 board marks calculation, algorithmic choice optimization, campus branch swap discovery, and institutional tiering.

---

## 1. Project Overview & Purpose

Navigating the official Tamil Nadu Engineering Admissions (TNEA) single-window counseling process administered by the Directorate of Technical Education (DoTE) is challenging for students and parents. With over 460 colleges, 110+ engineering disciplines, 7 communal categories, and shifting year-over-year cutoff thresholds, making informed choices is difficult.

**CollegeConnect** solves this by providing:
1. **Empirical Admission Feasibility:** Replaces guesswork with indicative probability estimates and **Safe**, **Target**, and **Reach** categorizations grounded on 113,218 verified admission records.
2. **Dual Assessment Modes:** Supports predictions by **Cutoff Mark** ($0.00 - 200.00$) or by **TNEA State Rank** ($1 - 250,000+$).
3. **AI Explanations (RAG):** Delivers explainable, natural-language counseling assessments powered by **Google Gemini** (`gemini-2.5-flash`), backed by a deterministic offline fallback engine.
4. **Campus Branch Alternatives:** Suggests alternative engineering streams within the same college campus if a student narrowly misses their primary branch.
5. **Strategic Choice Optimization:** Automatically balances choice lists into an optimal **20% Reach / 50% Target / 30% Safe** portfolio with 1-click export for the official DoTE portal.
6. **Institutional Classification:** Categorizes all 467 colleges into **Tier-1** (Premier), **Tier-2** (Established), and **Tier-3** (Regional) institutions based on 5-year cutoff percentiles and accreditation.

---

## 2. Key Features

* **Class 12 Board Cutoff Calculator:** Interactive in-page calculator computing official TNEA engineering aggregate marks:
  $$\text{Cutoff} = \text{Mathematics} + \frac{\text{Physics}}{2} + \frac{\text{Chemistry}}{2}$$
* **Cutoff & Rank Prediction Engines:** Multi-criteria filtering by Community (`OC`, `BC`, `BCM`, `MBC`, `SC`, `SCA`, `ST`), Districts (38 revenue districts), Branches (116 disciplines), Specific Colleges, and Institutional Tiers.
* **Deterministic Probability Scorer:** Evaluates weighted historical qualification match rates, historical cutoff cushions, latest-year margins, and multi-year trajectory shifts.
* **5-Year Cutoff Trend Chart:** Inline vector SVG line chart tracking year-over-year admission drift (2021–2025) with audit completeness flags (Full vs. Partial records).
* **Campus Branch Swap Explorer:** Identifies same-campus alternative disciplines with live score cushion ($+ / -$) and admission feasibility.
* **DoTE Choice Optimizer & Formatter:** Reorders choices into a strategic 20/50/30 distribution with direct clipboard copy formatted for the DoTE counseling entry portal, structured RFC-4180 CSV export, and publication-ready PDF download.
* **Dual-Theme Engine (Dark & Light Mirror):** Pixel-faithful mirror theme system with zero-FOUC initialization, instant navbar toggle, `localStorage` persistence, and WCAG AAA compliant text/badge contrast in both themes.
* **State Rank Matrix:** Empirical reference table mapping cutoff brackets against state rank distributions.
* **DoTE Counseling Quota Support:** Native support for General Academic counseling, 7.5% Government School preferential quota, and Special Category reservations (Sports, Ex-Servicemen, Differently Abled Persons) with contextual advisory guidance.

---

## 3. Technology Stack

| Layer | Technologies / Packages | Purpose |
|---|---|---|
| **Frontend** | HTML5, Vanilla JavaScript (ES6+), CSS3 (Custom Glassmorphism) | Lightweight, zero-framework, dependency-free reactive user interface |
| **Data Visualization** | Inline Dynamic Scalable Vector Graphics (SVG) | High-precision responsive trendline charts with no external CDN dependency |
| **Backend Framework** | Python 3.11, Flask 3.1.0, Werkzeug 3.1.3 | Modular REST API service and static asset server |
| **Database Engine** | MySQL Server 8.4 (InnoDB Storage Engine, `utf8mb4`) | Relational 3NF data store with composite B-Tree indexes |
| **Database Driver** | PyMySQL 1.1.1 | Pure-Python MySQL client with connection pooling and dictionary cursor |
| **AI / RAG** | Google GenAI SDK (`google-genai` 1.63.0), Gemini 2.5 Flash | Grounded natural language admission assessments and reasoning |
| **Data Processing** | Pandas 2.2.3, NumPy 2.2.3 | Ingestion ETL pipeline, unpivoting, and percentile tier clustering |
| **Configuration** | `python-dotenv` 1.0.1 | Environment-variable management (`.env`) |

---

## 4. System Architecture

```
+---------------------------------------------------------------------------------------------------+
|                                          CLIENT BROWSER                                           |
|                                                                                                   |
|   frontend/index.html                     frontend/styles.css               frontend/app.js       |
|   ┌──────────────────────────────┐        ┌────────────────────────┐        ┌──────────────────┐  |
|   │ - Prediction Input Form      │        │ - Glassmorphic Theme   │        │ - Form State Mgr │  |
|   │ - Class 12 Marks Calculator  │        │ - Modal Overlays       │        │ - SVG Renderer   │  |
|   │ - Tier & Quota Controls      │        │ - Badges & Tooltips    │        │ - REST Client    │  |
|   │ - Trend Chart Modal (SVG)    │        │ - Responsive Grid      │        │ - Choice Builder │  |
|   │ - Branch Swap Modal          │        └────────────────────────┘        │ - DoTE Formatter │  |
|   └──────────────────────────────┘                                          └──────────────────┘  |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  │ HTTP REST (JSON)
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                          FLASK BACKEND                                            |
|                                                                                                   |
|   backend/app.py (Canonical Entry Point & Static Server, port 5000)                               |
|   ├── Static Handler:  GET /                                                                      |
|   ├── Core APIs:       GET /api/predictions, GET /api/colleges, GET /api/tiers                    |
|   ├── Recommendations: GET /api/branch-swap, GET /api/historical                                  |
|   └── Optimizer:       POST /api/choices/optimize                                                 |
|                                                                                                   |
|   Registered Blueprints:                                                                          |
|   ├── backend/rank_routes.py      -> GET /api/rank-predictions                                    |
|   ├── backend/matrix_routes.py    -> GET /api/rank-matrix                                         |
|   ├── backend/rag_routes.py       -> GET/POST /api/rag-explanation                                |
|   ├── backend/rank_rag_routes.py  -> GET/POST /api/rank-rag-explanation                           |
|   └── backend/combined_routes.py  -> GET /api/combined-predictions                                |
+---------------------------------------------------------------------------------------------------+
                         │                                                   │
                         │ Ingests Retrieved Context                         │ Parameterized SQL
                         ▼                                                   ▼
+---------------------------------------------------+     +-----------------------------------------+
|                SCORING & RAG ENGINE               |     |             DATABASE LAYER              |
|                                                   |     |                                         |
|  backend/probability_service.py                   |     |  MySQL Server 8.4 (Port 3306)           |
|  - Dynamic 2021-2025 trajectory & margin drift    |     |  Database: collegeconnect               |
|                                                   |     |                                         |
|  backend/scoring.py                               |     |  Master Tables:                         |
|  - Deterministic qualification rate calculation   |     |  ├── colleges (467 rows)                |
|  - Probability score & tier assignment            |     |  │   - Tier-1: 69 institutions          |
|                                                   |     |  │   - Tier-2: 211 institutions         |
|  backend/rag.py                                   |     |  │   - Tier-3: 187 institutions         |
|  - Google GenAI SDK (gemini-2.5-flash)            |     |  ├── branches (116 rows)                |
|  - Offline Deterministic Grounded Fallback        |     |  └── historical_admissions              |
|                                                   |     |      (113,218 fact rows, 2021-2025)     |
+---------------------------------------------------+     +-----------------------------------------+
```

---

## 5. Important File Paths & Component Responsibilities

All paths listed below are verified, physical paths in the repository:

| Component | Path | Description & Responsibility |
|---|---|---|
| **Main Frontend HTML** | `frontend/index.html` | Single-page UI containing prediction inputs, Class 12 calculator, search filters, result cards, `#trendModal`, `#branchSwapModal`, and `#quotaAdvisoryBanner`. |
| **Main Frontend JavaScript** | `frontend/app.js` | Client controller handling state management, API requests, dynamic SVG line chart rendering, campus branch swap modal, choice list optimizer, and DoTE clipboard copy. |
| **Main CSS Stylesheet** | `frontend/styles.css` | Comprehensive design system implementing dark glassmorphism, responsive grid layout, SVG chart styling, and institutional tier badges. |
| **Main Flask Entry Point** | `backend/app.py` | Canonical application server registering all blueprints, serving static assets, and implementing `/api/predictions`, `/api/colleges`, `/api/tiers`, `/api/branch-swap`, and `/api/choices/optimize`. |
| **Delegating Entry Point** | `backend/site.py` | Standalone delegation script importing and running `app` from `backend.app`. |
| **Database Helper** | `backend/db.py` | Centralized database connection factory reading environment variables from `.env` and managing PyMySQL connections and safe closures. |
| **Probability Service** | `backend/probability_service.py` | Dynamic multi-year evaluator resolving latest cutoffs, calculating historical margins, and determining 5-year trajectory drift. |
| **Deterministic Scorer** | `backend/scoring.py` | Mathematical scoring algorithm producing probability percentages, Safe/Target/Reach classifications, and detailed reasoning text. |
| **Rank Routes Blueprint** | `backend/rank_routes.py` | Implements `/api/rank-predictions` for TNEA state rank queries with quota and institutional tier filtering. |
| **Rank Matrix Blueprint** | `backend/matrix_routes.py` | Implements `/api/rank-matrix` mapping cutoff brackets to empirical closing ranks. |
| **RAG Core Engine** | `backend/rag.py` | Google GenAI SDK client for `gemini-2.5-flash` with robust offline rule-based deterministic fallback generator. |
| **Cutoff RAG Routes** | `backend/rag_routes.py` | Implements `/api/rag-explanation` generating grounded AI explanations for cutoff queries. |
| **Rank RAG Routes** | `backend/rank_rag_routes.py` | Implements `/api/rank-rag-explanation` generating grounded AI explanations for rank queries. |
| **Database DDL Schema** | `database/schema.sql` | Authoritative MySQL 3NF schema script creating `colleges`, `branches`, `historical_admissions`, and composite B-Tree indexes. |
| **Database ETL Script** | `scripts/load_database.py` | Ingestion script that unpivots the 16,174 source offerings into 113,218 records and triggers post-load tier classification. |
| **Tier Classifier Script** | `scripts/classify_tiers.py` | Classifies all 467 colleges into Tier-1, Tier-2, and Tier-3 based on 5-year cutoff percentiles and autonomous accreditation. |
| **Scoring Module Test** | `scripts/test_scoring.py` | Direct unit test verifying deterministic probability scoring and reasoning formatting. |
| **System Verification Suite** | `scripts/verify_system.py` | End-to-end verification suite testing all 26 checkpoints across database, APIs, RAG, optimizer, and frontend assets. |
| **Active Environment File** | `.env` | Local configuration storing MySQL credentials and Gemini API key. |
| **Environment Template** | `.env.example` | Template documenting required environment variables for deployment. |
| **Python Dependencies** | `requirements.txt` | Complete list of pinned Python packages. |
| **Raw Dataset** | `data/integrated/tnea_integrated_master.csv` | Cleaned 5-year integrated TNEA master CSV (2021–2025). |

---

## 6. Installation & Setup Instructions

### Prerequisites
* **Operating System:** Windows 10/11, macOS, or Linux
* **Python:** Python 3.11 or later
* **MySQL:** MySQL Server 8.0+ or 8.4 LTS
* **Node.js (Optional):** Used for syntax verification of frontend scripts

### Step 1: Clone or Navigate to the Repository
```powershell
git clone https://github.com/sanjay-3309/CollegeConnect.git
cd CollegeConnect
```

### Step 2: Install Python Dependencies
```powershell
py -3.11 -m pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Create or edit `.env` in the project root:
```env
# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=collegeconnect
MYSQL_USER=root
MYSQL_PASSWORD=

# Google Gemini API Configuration
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash

# Application Environment
FLASK_ENV=development
```

> **Note on Gemini API Key:** If `GEMINI_API_KEY` is left blank, CollegeConnect operates transparently in **Offline Fallback Mode**, generating deterministic, grounded rule-based explanations without errors.

### Step 4: Initialize and Load the Database
1. Ensure MySQL Server is running on port 3306.
2. Initialize schema and ingest the 113,218 admission records:
   ```powershell
   py -3.11 scripts/load_database.py
   ```
3. Classify institutional tiers (automatically run by `load_database.py`):
   ```powershell
   py -3.11 scripts/classify_tiers.py
   ```

---

## 7. How to Run the Application

### Start the MySQL Daemon & Flask Application
You can start the services using either the command line or the provided Windows batch scripts:

**Option 1: Using Convenient Launcher Scripts**
* Start MySQL: Double-click or run `start_mysql.bat`. On first use, it initializes the ignored local data directory.
* Start Application: Double-click or run `run_app.bat`

**Option 2: Using Command Line**
```powershell
# In terminal 1 (or allow backend auto-recovery):
start_mysql.bat

# In terminal 2:
py -3.11 backend/app.py
```
> **Self-Healing Note:** The Flask backend (`backend/db.py`) includes an automatic connection manager that detects if the local MySQL daemon is down and attempts to spawn `mysqld` automatically.

* The server starts locally at **`http://127.0.0.1:5000/`**.
* Open your browser and navigate to `http://127.0.0.1:5000/`.

---

## 8. How to Run the Verification & Test Suite

CollegeConnect includes an automated end-to-end verification suite that validates the entire stack:

```powershell
py -3.11 scripts/verify_system.py
py -3.11 scripts/verify_theme_system.py
py -3.11 scripts/test_modal_and_exports.py
```

### Expected Output:
```text
======================================================================
COLLEGECONNECT FULL SYSTEM END-TO-END VERIFICATION
======================================================================

--- 1. DATABASE INTEGRITY ---
  [PASS] Database Connection (MySQL connected on port 3306)
  [PASS] Colleges Count (467 colleges)
  [PASS] Branches Count (116 branches)
  [PASS] Historical Admissions Count (113,218 records)
  [PASS] Institutional Tiers Populated (T1: 69, T2: 211, T3: 187)

--- 2. CORE BACKEND APIS ---
  [PASS] GET /api/health
  [PASS] GET /api/db-test
  [PASS] GET /api/districts (38 districts)
  [PASS] GET /api/branches (116 branches)
  [PASS] GET /api/tiers (3 tiers returned)
  [PASS] GET /api/colleges?tier=Tier-1 (69 Tier-1 colleges)

--- 3. PREDICTION & QUOTA ENGINES ---
  [PASS] Cutoff Prediction Basic (25 candidates returned)
  [PASS] Cutoff Prediction Fields (Probability: 6.5%, Tier: Reach)
  [PASS] Cutoff Prediction Tier-1 Filter (30 Tier-1 candidates)
  [PASS] Special Quota 7.5% Handling (Advisory note populated)
  [PASS] Rank Prediction (30 candidates returned)
  [PASS] Cutoff Prediction Multi-Filter (District, Branch, College) (1 filtered candidate)
  [PASS] Rank Matrix Basic (100 records returned)
  [PASS] Rank Matrix College Filter (26 records for college 2006)
  [PASS] Rank Matrix District & Branch Filter (2 records returned)

--- 4. RAG, HISTORICAL & RECOMMENDATIONS ---
  [PASS] Historical 5-Year Trajectory (5 years: 2021-2025)
  [PASS] Campus Branch Swap Alternatives (18 branches on campus)
  [PASS] Choice Optimizer Algorithm (Balanced 20/50/30 distribution)
  [PASS] RAG Explanation (Cutoff) (Model: Deterministic Scorer (Offline Fallback))
  [PASS] RAG Explanation (Rank) (Model: Deterministic Scorer (Offline Fallback))

--- 5. FRONTEND STATIC ASSETS & JAVASCRIPT ---
  [PASS] Index.html Modal & Widget Markup (All 6 UI widgets present)
  [PASS] Styles.css Modals & Badges (Modal, tier badge & quota advisory CSS verified)
  [PASS] App.js Controllers Served (Controllers verified)
  [PASS] Frontend App.js Syntax (Node.js syntax parser passed)

======================================================================
VERIFICATION SUMMARY: 29/29 checks passed (100.0%)
======================================================================
```

To run the scoring unit test:
```powershell
py -3.11 scripts/test_scoring.py
```

---

## 9. API Overview & Key Endpoints

| Endpoint | Method | Query / Body Parameters | Response Description |
|---|:---:|---|---|
| `/api/health` | GET | None | Backend health and service status |
| `/api/db-test` | GET | None | MySQL database connectivity check |
| `/api/districts` | GET | None | List of all 38 Tamil Nadu districts |
| `/api/branches` | GET | None | List of all 116 engineering branches |
| `/api/tiers` | GET | None | List of 3 institutional tiers with counts and descriptions |
| `/api/colleges` | GET | `district`, `branch_code`, `tier` | Search colleges with multi-value and tier filtering |
| `/api/predictions` | GET | `cutoff_mark`, `community`, `district`, `branch_code`, `tier`, `quota`, `limit` | Cutoff admission predictions with probability scores and trajectories |
| `/api/rank-predictions` | GET | `state_rank`, `community`, `district`, `branch_code`, `tier`, `quota`, `limit` | State rank admission predictions |
| `/api/rank-matrix` | GET | `community`, `district`, `branch_code`, `college_code`, `limit` | Closing rank matrix across institutions and disciplines |
| `/api/historical` | GET | `college_code`, `branch_code`, `community`, `quota` | 5-year chronological cutoff and closing rank records (2021–2025) |
| `/api/branch-swap` | GET | `college_code`, `cutoff_mark`, `state_rank`, `community`, `quota` | Same-campus branch alternatives with cushion marks and tiers |
| `/api/choices/optimize` | POST | JSON: `{"choices": [...], "target_count": 15}` | Algorithmic 20% Reach / 50% Target / 30% Safe choice list optimizer |
| `/api/rag-explanation` | GET/POST | `cutoff_mark`, `community`, `college_code` | AI-grounded cutoff admission assessment (Gemini or offline fallback) |
| `/api/rank-rag-explanation` | GET/POST | `state_rank`, `community`, `college_code` | AI-grounded state rank admission assessment |

---

## 10. Project Directory Structure

```text
CollegeConnect/
├── .env                                  # Active environment configuration
├── .env.example                          # Environment template
├── .gitignore                            # Version control exclusion rules
├── CURRENT_PROJECT_STATE.md              # Authoritative state and verification audit
├── DATABASE_SCHEMA.md                    # Relational database schema specification
├── PROJECT_PLAN.md                       # Comprehensive engineering plan
├── PROJECT_IMPLEMENTATION_REPORT.md      # Phase-by-phase implementation and test report
├── CollegeConnect_Work_Plan.md           # Completed work plan checklist
├── README.md                             # Main project documentation (this file)
├── requirements.txt                      # Pinned Python package dependencies
│
├── backend/
│   ├── app.py                            # Canonical Flask entry point & static server
│   ├── site.py                           # Delegating runner script
│   ├── db.py                             # PyMySQL connection factory & safe_close helper
│   ├── probability_service.py            # Dynamic multi-year trajectory & margin calculations
│   ├── scoring.py                        # Deterministic scoring algorithm & tiering
│   ├── rag.py                            # Google GenAI Gemini client & deterministic fallback
│   ├── rag_routes.py                     # Cutoff RAG explanation blueprint
│   ├── rank_rag_routes.py                # Rank RAG explanation blueprint
│   ├── rank_routes.py                    # State rank prediction blueprint
│   ├── matrix_routes.py                  # Closing rank matrix blueprint
│   ├── combined_routes.py                # Combined dual-mode prediction blueprint
│   └── archive/                          # Archived legacy implementations (predictor.py, etc.)
│
├── frontend/
│   ├── index.html                        # Single-page interface & dialog modals
│   ├── app.js                            # Client controllers, SVG charts, and choice optimizer
│   └── styles.css                        # Design system & dark glassmorphism styling
│
├── database/
│   └── schema.sql                        # Production MySQL schema DDL & composite indexes
│
├── data/
│   └── integrated/
│       └── tnea_integrated_master.csv    # 5-year master TNEA dataset (16,174 offerings)
│
└── scripts/
    ├── load_database.py                  # ETL ingestion pipeline with integrity assertions
    ├── classify_tiers.py                 # Institutional tier classification script
    ├── test_scoring.py                   # Scoring module verification unit test
    └── verify_system.py                  # Full system 26-checkpoint verification suite
```

---

## 11. Current Project Status & Completion

* **Overall Status:** **100% Implemented & Verified (Production-Ready Architecture)**
* **Verification Score:** **29/29 Checks Passed (100.0%)**
* **Database State:** 467 Colleges, 116 Branches, 113,218 Fact Records, 0 NULL Tiers.
* **Code Cleanliness:** Conflicting entry points consolidated; legacy prototypes archived in `backend/archive/`; zero unhandled exceptions.

---

## 12. Known Limitations & Domain Notes

1. **DoTE Quota Structure:** In official TNEA counseling, the 7.5% Government School preferential reservation and Special Categories (Sports, Ex-Servicemen, Differently Abled Persons) operate on dedicated preliminary counseling lists administered directly by DoTE without merged general cutoffs. CollegeConnect models these using the primary General Academic historical dataset as a reference baseline and provides explicit advisory notices (noting that 7.5% cutoffs typically run 15–30 marks lower).
2. **Gemini API Connectivity:** When no `GEMINI_API_KEY` is provided or when network quotas are exceeded, the system automatically uses the internal rule-based deterministic generator, guaranteeing that the platform remains fully functional without crashing.
3. **Sparse ST/SCA Branch Records:** Certain specialized disciplines (e.g., Ceramic Technology, Marine Engineering) had zero historical ST allotments across recent counseling years. The database preserves these as explicit SQL `NULL` values rather than misleading zeros to protect historical match-rate accuracy.
