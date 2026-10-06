# CollegeConnect – Your TNEA College Prediction Assistant
## Comprehensive Project Engineering Plan & Architecture Specification

**Project Context:** Academic Application Development Lab (23N511), Department of Computer Science and Engineering, PSG College of Technology  
**Document Status:** Approved & Verified Architectural Plan (Implemented & Operating System)  
**Date:** October 2026 (Updated & Verified)  

---

## 1. Executive Summary & Core Constraints

CollegeConnect is an academic web application designed to assist Tamil Nadu Engineering Admissions (TNEA) aspirants in navigating college and branch selections across Tamil Nadu. The system enables students to compute aggregate cutoff scores from board marks or input their official state ranks, evaluates their admission viability across 5 years of historical cutoff and rank datasets (2021–2025), and leverages a Retrieval-Augmented Generation (RAG) pipeline powered by Google Gemini for grounded reasoning, trend explanation, and choice-list optimization.

### Core Directives & Ground Rules
1. **No Logic Duplication from Demo Application:** The existing demo application repository (`TNEA-Cuttoff-Predictor`) is strictly a UI/UX layout and visual reference. Its frontend heuristics, mock JavaScript data (`js/data.js`), client-side probability math (`js/mlEngine.js`), and simulated calculations must **not** be used as backend or prediction logic.
2. **Authoritative Data Source:** The single source of truth is the verified, cleaned 5-year TNEA dataset (2021–2025) comprising **16,174 integrated records**, 467 unique engineering colleges, and 116 branch codes across 7 standard reservation categories (OC, BC, BCM, MBC, SC, SCA, ST).
3. **Database Architecture:** Relational data will be stored and indexed in **MySQL**. Logical entities (`College`, `CutoffRecord`) outlined in the lab report will be translated into a normalized, high-performance physical schema following detailed dataset inspection.
4. **AI/RAG Pipeline:** A Retrieval-Augmented Generation (RAG) architecture using **Google Gemini** will be integrated to provide explainable admissions assessments and contextual counseling recommendations, strictly grounded on retrieved MySQL records to prevent hallucinations.
5. **Incremental Delivery:** The project is executed modularly in discrete phases—from schema design and data ingestion to deterministic retrieval, RAG integration, and responsive frontend dashboard assembly.

---

## 2. Proposed Project Architecture

CollegeConnect follows a decoupled, 5-tier layered architecture designed for separation of concerns, deterministic data accuracy, and transparent AI reasoning.

```
+-----------------------------------------------------------------------------------+
|                            1. USER INTERFACE LAYER                                |
|  - Modern Single-Page Dashboard (Glassmorphism design inspired by demo UI)        |
|  - Cutoff Calculator (Maths, Physics, Chemistry) / State Rank Input Form          |
|  - Multi-Dimensional Filter Controls (Category, Quotas, District, Branch, Tier)   |
|  - Prediction Results Grid with Probability Tiers (Safe / Target / Reach)         |
|  - 5-Year Cutoff Trend Modal (Chart.js / SVG) & Branch Swap Modal                 |
|  - DoTE Choice List Optimizer & Formatter                                         |
|  - State Rank Matrix Reference Table                                              |
+-----------------------------------------+-----------------------------------------+
                                          | JSON over REST APIs
                                          v
+-----------------------------------------------------------------------------------+
|                           2. BACKEND API SERVICE LAYER                            |
|  - HTTP Router & Request Validation (Mark bounds, rank validity, quota enum)      |
|  - Cutoff Normalization Engine (Maths + Physics/2 + Chemistry/2)                  |
|  - API Controller Endpoints (/api/predict, /api/choices, /api/matrix, /api/rag)   |
|  - Response Serializer & Pagination Handler                                       |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        3. RETRIEVAL & QUERY ENGINE LAYER                          |
|  - Parameterized Dynamic SQL Generator                                            |
|  - Multi-Year Historical Aggregator (2021–2025 cutoff and rank matching)          |
|  - Historical Match Rate Calculator (Years qualified / Active recorded years)     |
|  - 5-Year Trajectory & Cutoff Drift Calculator                                    |
|  - Context Assembler for RAG Pipeline                                             |
+--------------------+------------------------------------+-------------------------+
                     |                                    |
                     v                                    v
+------------------------------------+   +------------------------------------------+
|       4. DATABASE LAYER (MySQL)     |   |         5. RAG & AI REASONING LAYER      |
|  - Normalized Relational Tables:   |   |   (Google Gemini Integration)            |
|    * colleges                      |   |  - Grounded Prompt Synthesizer           |
|    * branches                      |   |  - Google Gemini Model Client            |
|    * cutoff_rank_records           |   |  - Deterministic Context Injection       |
|    * quota_matrix                  |   |  - Admission Assessment Explanation Gen  |
|  - Optimized B-Tree Indices:       |   |  - Strategic Choice Justification        |
|    (community, cutoff_mark)        |   |  - Hallucination Guardrails & Fallbacks  |
|    (college_code, branch_code)     |   +------------------------------------------+
+------------------------------------+
```

---

## 3. Major Modules Specification

### Module 1: User Input & Cutoff Calculation Engine
* **Purpose:** Collects, validates, and normalizes candidate credentials.
* **Functional Scope:**
  * Mode A: Academic Marks Entry — Mathematics ($M \in [0, 100]$), Physics ($P \in [0, 100]$), Chemistry ($C \in [0, 100]$) with steps of 0.5.
  * TNEA Cutoff Computation Formula:
    $$\text{TNEA Cutoff} = M + \frac{P}{2} + \frac{C}{2} \quad (\text{Scale: } 0.00 \text{ to } 200.00)$$
  * Mode B: State Rank Entry — Candidate overall TNEA state rank ($R \ge 1$).
  * Input Sanitization: Rejects out-of-range marks, negative values, and non-numeric characters.

### Module 2: TNEA Historical Database & Ingestion Module
* **Purpose:** Manages the relational storage and indexing of official TNEA historical data.
* **Functional Scope:**
  * Ingests the 16,174 integrated records spanning years 2021 through 2025.
  * Preserves data integrity: Handles legitimate missing cutoff/rank values (such as non-allotted ST/SCA seats) as structured SQL `NULL` values rather than arbitrary zeroes.
  * Provides optimized query abstractions for historical lookups by year, college, branch, and community.

### Module 3: Historical Retrieval & Multi-Criteria Filtering Engine
* **Purpose:** Retrieves eligible college-branch opportunities based on student credentials and constraints.
* **Functional Scope:**
  * Cutoff Comparison: $\text{Student Cutoff} \ge \text{Historical Cutoff}$.
  * Rank Comparison: $\text{Student Rank} \le \text{Historical Closing Rank}$.
  * Filter Dimensions:
    * **Community Category:** OC, BC, BCM, MBC, SC, SCA, ST.
    * **7.5% Government School Quota:** Preferential seat reservation filter.
    * **Special Quota:** Differently Abled, Sports Persons, Ex-Servicemen.
    * **Geographic / District:** Single or multi-district filtering (e.g., Chennai, Coimbatore, Madurai).
    * **Engineering Branch:** Specific branch streams (e.g., Computer Science, Mechanical, ECE).
    * **College Selector:** Filter by specific college code or institution name.
    * **Institutional Tier:** Premier (Tier-1), Reputed (Tier-2), Affiliated (Tier-3).

### Module 4: Admission Assessment & Scoring Engine
* **Purpose:** Provides a data-driven historical assessment for each candidate college-branch pair.
* **Functional Scope:**
  * Computes **Historical Match Rate**:
    $$\text{Match Rate} = \frac{\sum_{y \in Y_{\text{active}}} \mathbb{I}(\text{Candidate Qualifies in year } y)}{|Y_{\text{active}}|}$$
  * Probability Classification Tiers:
    * **Safe (>85% historical match / comfortable cutoff cushion):** Student cutoff exceeds past cutoffs by $\ge 2.5$ marks or rank is well within closing bounds.
    * **Target (50% – 85% historical match):** Student cutoff is within $\pm 2.0$ marks of historical average cutoffs.
    * **Reach (<50% historical match / ambitious):** Cutoff is slightly below historical cutoffs (within reach gap $\le 3.0$ marks).
  * Computes 5-year cutoff shift ($\Delta = \text{Cutoff}_{2025} - \text{Cutoff}_{2021}$) and historical trend trajectory (Upward, Stable, Downward).

### Module 5: RAG & Gemini Explanation Engine
* **Purpose:** Delivers natural language explanations, risk justifications, and alternative strategy advice.
* **Functional Scope:**
  * Context Formulation: Constructs compact prompts injecting student scores, top matching colleges, cutoff cushions, and 5-year trends.
  * Grounded Generation: Google Gemini analyzes the retrieved data to explain *why* an option is Safe, Target, or Reach.
  * Smart Campus Branch Swaps: Identifies alternate engineering branches within the same campus if a candidate narrowly misses their primary choice.
  * Strictly bounded: Enforces guardrails so Gemini never invents hypothetical cutoff figures.

### Module 6: DoTE Choice Optimizer Module
* **Purpose:** Generates a strategically balanced preference list for the official DoTE single-window counseling portal.
* **Functional Scope:**
  * Algorithmic Strategy: Suggests a prioritized choice list balancing:
    * 20% Reach / Ambitious choices (Dream institutions)
    * 50% Target choices (Realistic probability)
    * 30% Safe choices (Guaranteed safety nets)
  * Manual List Management: Drag-and-drop or re-order priority rankings.
  * Export Facilities:
    * Formatted text output tailored for direct copy-pasting into the official DoTE portal (`tneaonline.org`).
    * Structured CSV export.

### Module 7: State Rank Matrix Analytical Module
* **Purpose:** Provides an independent empirical reference matrix mapping cutoff bands to state ranks.
* **Functional Scope:**
  * Renders benchmark cutoff brackets (e.g., 199.5–200.0, 198.0–199.49, ..., 110.0–159.99).
  * Displays estimated state rank spreads, student competition density, and typical institutional allotment spectrums.
  * Operates directly on the historical dataset independently of individual student inputs.

### Module 8: Frontend Dashboard & Interactive UI Module
* **Purpose:** Delivers an intuitive, accessible, and high-performance interface.
* **Functional Scope:**
  * Unified single-page responsive layout inspired by modern glassmorphic aesthetics.
  * Real-time reactive updates as marks or filters change.
  * Interactive modal dialogs: 5-year cutoff trend visualization, smart branch swaps, and DoTE export formatter.

---

## 4. End-to-End Data Flow

```
[Candidate Input]
  │  (Marks: Maths, Physics, Chemistry OR State Rank + Category & Quotas)
  ▼
[Input Validation & Normalization]
  │  (Compute Cutoff out of 200.00; validate bounds)
  ▼
[Query Construction & Parameter Binding]
  │  (Build dynamic SQL for community, quotas, districts, branches)
  ▼
[MySQL Database Execution]
  │  (Indexed query against 16,174 records spanning 2021–2025)
  ▼
[Deterministic Scoring Engine]
  │  (Compute Historical Match Rate, Cutoff Delta, Probability Tier)
  ▼
[Context Assembly for RAG Pipeline]
  │  (Extract candidate profile + top retrieved matches & trend metrics)
  ▼
[Google Gemini API Invocation]
  │  (Generate natural language admission rationale & choice strategy)
  ▼
[Payload Serialization & JSON API Response]
  │  (Matches array, summary metrics, RAG narrative, choice optimization)
  ▼
[Frontend Dashboard Rendering]
  │  (Results table, Safe/Target/Reach badges, Chart.js trends, DoTE export)
```

---

## 5. Database Planning (MySQL)

### 5.1 Dataset Characterization & Inspection Findings
The project's authoritative data source is the integrated 5-year dataset (`tnea_integrated_master.csv`) exhibiting the following verified attributes:
* **Record Count:** Exactly 16,174 rows covering academic admission years 2021, 2022, 2023, 2024, and 2025.
* **Institutions & Programs:** 467 unique college codes, 116 unique branch codes across 39 Tamil Nadu revenue districts and 9 college categories (CEG Departments, Government Colleges, Government Aided, Self-Financing, etc.).
* **Category Representation in Source Data:** Source files represent reservation categories as wide columns (`cutoff_oc`, `cutoff_bc`, `cutoff_bcm`, `cutoff_mbc`, `cutoff_sc`, `cutoff_sca`, `cutoff_st` and matching `rank_*` columns).
* **Missing Value Semantics:** Missing entries in categories such as ST or SCA reflect programs where no seats were allotted under that quota for that academic year. They must be maintained as `NULL` to avoid corrupting average and match-rate calculations.

### 5.2 Proposed Relational Schema Design

```
+---------------------------------------------------------------------------------+
|                                 colleges                                        |
+---------------------------------------------------------------------------------+
| college_code     INT             PRIMARY KEY (Official TNEA Code, e.g., 1, 2001)|
| college_name     VARCHAR(255)    NOT NULL                                       |
| district         VARCHAR(100)    NOT NULL (e.g., CHENNAI, COIMBATORE)           |
| college_type     VARCHAR(100)    NOT NULL (e.g., CEG DEPTS, GOVT, SFI)          |
| institutional_tier VARCHAR(20)   NULL (Tier-1, Tier-2, Tier-3)                  |
+---------------------------------------------------------------------------------+
                                      |
                                      | 1
                                      |
                                      | N
+---------------------------------------------------------------------------------+
|                                cutoff_records                                   |
+---------------------------------------------------------------------------------+
| record_id        BIGINT AUTO_INC PRIMARY KEY                                    |
| college_code     INT             FOREIGN KEY -> colleges(college_code)          |
| branch_code      VARCHAR(10)     NOT NULL (e.g., CS, EC, ME, IT)                |
| branch_name      VARCHAR(255)    NOT NULL                                       |
| year             SMALLINT        NOT NULL (2021, 2022, 2023, 2024, 2025)        |
| community        VARCHAR(10)     NOT NULL (OC, BC, BCM, MBC, SC, SCA, ST)       |
| quota_type       VARCHAR(50)     NOT NULL DEFAULT 'GENERAL' (GENERAL, 7.5_GOVT) |
| cutoff_mark      DECIMAL(6,3)    NULL (Recorded cutoff mark out of 200.00)      |
| closing_rank     INT             NULL (Official DoTE closing rank)              |
| is_partial       TINYINT(1)      DEFAULT 0 (Allotment completeness flag)        |
+---------------------------------------------------------------------------------+
```

### 5.3 Database Indexing Strategy
To ensure sub-50ms API response times across dynamic multi-field filtering:
* `idx_community_cutoff`: `(community, quota_type, cutoff_mark)`
* `idx_community_rank`: `(community, quota_type, closing_rank)`
* `idx_lookup_composite`: `(college_code, branch_code, year, community)`
* `idx_district_filter`: `(district)`
* `idx_branch_filter`: `(branch_code)`

### 5.4 Resolved Architectural & Database Decisions
* `[RESOLVED & IMPLEMENTED]` **Normalized (Tall) Ingestion Format:** Implemented in `database/schema.sql` and `scripts/load_database.py`. The database stores 113,218 atomic rows in `historical_admissions` across 467 colleges and 116 branches, with composite B-Tree indexes on `(community, quota, year, cutoff_mark)` and `(college_code, branch_code, year, community, quota)` achieving sub-10ms queries.
* `[RESOLVED & IMPLEMENTED]` **7.5% Government Quota & Special Quotas:** Audited source dataset confirmed raw 2021–2025 records contain General Academic allotments. Quota handling is implemented via `resolve_quota` backend layer and frontend DoTE counseling advisory banners, using baseline general cutoffs with clear statutory advisory text rather than fabricating synthetic data.
* `[RESOLVED & IMPLEMENTED]` **Institutional Tier Classification:** Implemented via data-driven script `scripts/classify_tiers.py`. All 467 institutions are classified into Tier-1 (69), Tier-2 (211), and Tier-3 (187) based on 2024–2025 closing cutoff profiles and institutional status (0 NULL tiers).

---

## 6. RAG (Retrieval-Augmented Generation) & Gemini Planning

### 6.1 Purpose of RAG in CollegeConnect
Unlike generic chatbots or unexplainable black-box machine learning models, CollegeConnect uses Google Gemini specifically to provide **grounded, context-aware reasoning** over actual historical cutoff records retrieved from MySQL.

### 6.2 Three-Stage RAG Execution Flow
1. **Context Retrieval:**
   * SQL queries extract the 5-year cutoff and rank trajectory for colleges matching the student’s profile.
   * Nearest-neighbor records (colleges with closing cutoffs within $\pm 2.0$ marks of the student) are retrieved.
2. **Context Assembly & Grounding:**
   * Context payload structured with explicit facts:
     ```json
     {
       "student_cutoff": 191.00,
       "community": "BC",
       "target_college": "PSG College of Technology (2001)",
       "branch": "Computer Science and Engineering (CS)",
       "history": [
         {"year": 2021, "cutoff": 196.50, "rank": 620},
         {"year": 2022, "cutoff": 197.00, "rank": 580},
         {"year": 2023, "cutoff": 196.75, "rank": 610},
         {"year": 2024, "cutoff": 197.25, "rank": 540},
         {"year": 2025, "cutoff": 197.50, "rank": 510}
       ],
       "gap": -6.50,
       "match_rate": "0/5 years (0%)"
     }
     ```
3. **Generative Assessment via Gemini:**
   * Gemini evaluates the gap and generates:
     * Clear assessment rationale: *“At 191.00, admission to PSG CSE under BC quota is highly ambitious (Reach), as the 5-year cutoff has remained strictly above 196.50.”*
     * Actionable alternative suggestion: *“Consider PSG Robotics & Automation or CIT Coimbatore CSE where BC cutoffs averaged 191.20.”*

### 6.3 Prompt Architecture & Guardrails
* **Anti-Hallucination Directives:** The system prompt strictly prohibits Gemini from quoting cutoff figures not present in the injected context.
* **Deterministic Fallback:** If the Gemini API experiences network timeouts, rate limiting, or service interruptions, the backend automatically falls back to deterministic rule-based explanations without breaking the user experience.
* **Model Selection:** `gemini-1.5-flash` or `gemini-2.0-flash` for high-speed, cost-effective inference suitable for interactive web applications.

---

## 7. Frontend Planning

### 7.1 Visual Layout & UX Design (Inspired by Demo Interface)
The frontend interface will adopt the visual polish and dashboard layout demonstrated in the demo UI, engineered with modern web standards:
* **Theme:** Professional dark glassmorphism theme (`#0f172a` slate palette with cyan `#38bdf8` and indigo `#818cf8` accents).
* **Navigation Header:** Brand logo, title ("CollegeConnect – 2026 TNEA Intelligence"), tab navigators, and PWA manifest support.
* **Main Tab 1: Cutoff & Predictor View:**
  * Top Banner: Dynamic state rank estimation based on Class 12 score distributions.
  * Left Sidebar: Cutoff score calculator (real-time mark inputs), community selector, quota toggles, district/branch filters, and probability tier selectors.
  * Right Main Viewport: Reactive results table showing College Name, Branch, 2025 Cutoff, Admission Probability Badge (Safe/Target/Reach), 5-Year Cutoff Shift, and Action buttons ("Add to Choices", "Trend Chart", "Branch Swap").
* **Main Tab 2: DoTE Choice List Optimizer:**
  * Interactive choice card queue with drag-to-reorder prioritization.
  * Distribution health-check widget (verifying balance between Safe, Target, and Reach choices).
  * Direct DoTE portal copy-paste export modal and CSV download.
* **Main Tab 3: State Rank Matrix:**
  * Full empirical reference table mapping cutoff ranges to historical state rank brackets and competition density.

### 7.2 Resolved Frontend Implementation Decisions
* `[RESOLVED & IMPLEMENTED]` **Frontend Framework Choice:** Option A selected and implemented: Pure Semantic HTML5 (`frontend/index.html`) + Modular Vanilla JavaScript (`frontend/app.js`) + Modern CSS3 Glassmorphism (`frontend/styles.css`). This provides zero external build dependencies, instant browser rendering, and full client-side state management for the choice optimizer, filters, and RAG dialogs.
* `[RESOLVED & IMPLEMENTED]` **Data Visualization Engine:** Built-in responsive dynamic SVG line chart engine implemented directly in `frontend/app.js` and `frontend/styles.css`. Renders 5-year cutoff and rank trajectories, data points, tooltips, and axes without external CDN dependencies or rendering lag.

---

## 8. Implementation Phases (Incremental & Modular)

All implementation phases have been successfully executed, integrated, and verified:

### Phase 1: Environment Setup & Data Inspection `[COMPLETED]`
* Verified Python 3.12, PyMySQL, and MySQL 8.4 database environments.
* Completed structural and exploratory data analysis (EDA) on all 16,174 integrated records in `data/integrated/tnea_integrated_master.csv`.
* Verified column definitions, null value distributions across categories (OC, BC, BCM, MBC, SC, SCA, ST), and category-specific ranges.

### Phase 2: MySQL Schema Design & ETL Ingestion Pipeline `[COMPLETED]`
* Formulated and executed 3NF normalized DDL in `database/schema.sql` (`colleges`, `branches`, `historical_admissions`).
* Implemented and executed ETL pipeline in `scripts/load_database.py`, ingesting 467 colleges, 116 branches, and 113,218 historical admission slots into `tnea_db`.
* Executed data-driven classification in `scripts/classify_tiers.py`, populating `institutional_tier` across all 467 institutions (Tier-1: 69, Tier-2: 211, Tier-3: 187, 0 NULLs).
* Verified database integrity: zero orphaned records, zero unmapped codes, and full foreign-key enforcement.

### Phase 3: Core Backend & Deterministic Retrieval Engine `[COMPLETED]`
* Developed production Flask 3.1 backend application service (`backend/app.py`, `backend/db.py`, `backend/scoring.py`, `backend/probability_service.py`).
* Implemented Cutoff Score Calculator ($M + P/2 + C/2$) and State Rank evaluation engine.
* Built parameterized SQL query engine with sub-10ms response times for community, quota, district, branch, and tier filters.
* Implemented deterministic multi-year scoring: historical match rate ($\ge 85\%$ Safe, $50\%-85\%$ Target, $<50\%$ Reach), cutoff cushion, and 5-year trajectory drift.

### Phase 4: State Rank Matrix & Choice Optimizer Logic `[COMPLETED]`
* Built State Rank Matrix API (`/api/matrix`, `/api/matrix/summary`) in `backend/matrix_routes.py` mapping cutoff bands to empirical rank spreads.
* Built State Rank prediction routes (`/api/predict-rank`) in `backend/rank_routes.py`.
* Implemented DoTE Choice Optimizer engine in `frontend/app.js` with 20% Reach / 50% Target / 30% Safe strategy, interactive re-ordering, and DoTE/CSV export modals.

### Phase 5: Google Gemini RAG Pipeline Integration `[COMPLETED]`
* Implemented Gemini AI service in `backend/rag.py` using `google-genai` SDK (`gemini-2.5-flash`).
* Mounted contextual RAG routes in `backend/rag_routes.py` (`/api/rag/assess`, `/api/rag/swaps`, `/api/rag/explain-choices`) and `backend/rank_rag_routes.py`.
* Implemented strictly grounded prompts and resilient deterministic fallback routines ensuring zero user disruption during API rate-limiting or offline execution.

### Phase 6: Frontend Development & API Binding `[COMPLETED]`
* Built unified single-page glassmorphism dashboard in `frontend/index.html`, `frontend/app.js`, and `frontend/styles.css`.
* Implemented dual input modes (Marks $\to$ Cutoff and State Rank) with real-time reactive validation.
* Engineered inline responsive dynamic SVG line chart engine for 5-year cutoff and rank trajectories without external dependencies.
* Wired up interactive modals: 5-year trend visualization, smart campus branch swaps, and DoTE choice export formatter.

### Phase 7: System Integration & End-to-End Hardening `[COMPLETED]`
* Consolidated server entry point in `backend/app.py`, serving both backend REST API endpoints and static frontend dashboard on port 5000.
* Integrated responsive DoTE counseling advisory banners for 7.5% Government School and Special Quotas.
* Implemented automated end-to-end verification suite in `scripts/verify_system.py`.

---

## 9. Testing & Quality Assurance Plan

### 9.1 Unit Testing `[VERIFIED]`
* **Cutoff Calculation Tests:** Validated formula accuracy across edge inputs (all zeros, 200.0, fractional half-marks, float precision).
* **Input Validation Tests:** Verified rejection of negative values, marks $>100$, and malformed rank inputs.
* **Scoring Logic Tests:** Verified boundary transitions between Safe ($\ge 85\%$), Target ($50\% - 85\%$), and Reach ($<50\%$) classifications.

### 9.2 Data Integrity & Database Testing `[VERIFIED]`
* **Reconciliation Assertions:** Verified 100% numerical parity across all 113,218 records in MySQL against raw master CSV data.
* **Missing Value Handling Tests:** Confirmed that categories with sparse historical allotments (e.g., ST, SCA) correctly maintain SQL `NULL` without distorting match rates or raising exceptions.
* **Query Performance Profiling:** Filtered multi-table join queries execute in under 15 milliseconds.

### 9.3 RAG & Gemini Verification `[VERIFIED]`
* **Grounding & Guardrails:** Confirmed prompt structures inject only verified MySQL cutoff rows; Gemini output verified for hallucination prevention.
* **Fallback Resilience:** Verified that simulated API key absence or network timeout seamlessly triggers deterministic rule-based explanations with HTTP 200 responses.

### 9.4 User Acceptance & Counseling Scenario Testing `[VERIFIED]`
* **Benchmark Profile Validation:** Tested with high-cutoff ($>195$), competitive ($180–195$), moderate ($150–180$), and vocational profiles.
* **Choice List Integrity:** Verified that generated DoTE option lists contain valid college codes, valid branch codes, and conform to official DoTE counseling entry specifications.

---

## 10. Integration Phases

```
Stage 1: Raw Data (16,174 offerings) ───[scripts/load_database.py]───> MySQL Database (113,218 rows)
Stage 2: MySQL Database ───[backend/db.py]───> Backend Retrieval API
Stage 3: Backend Retrieval API ───[backend/scoring.py]───> Deterministic Scoring & Tiers
Stage 4: Scoring + Context ───[backend/rag.py]───> Google Gemini RAG (with Fallback)
Stage 5: Gemini Output + Scores ───[backend/app.py]───> Frontend Glassmorphism UI (frontend/)
```

---

## 11. Technical Risks, Mitigations & Resolutions

| Risk / Architectural Decision | Category | Impact | Implemented Resolution & Status |
| :--- | :--- | :--- | :--- |
| **Backend Framework Selection** | Architecture | Medium | **[RESOLVED]** Selected Flask 3.1 with modular Blueprints. Lightweight, high-performance, and unified static serving via `backend/app.py`. |
| **Gemini API Quota & Latency** | AI / RAG | High | **[RESOLVED]** RAG triggered asynchronously on-demand via modal dialogs. Instant deterministic fallback guarantees zero downtime and instant responses. |
| **Sparse Data in ST / SCA Categories** | Data Quality | Medium | **[RESOLVED]** Preserved SQL `NULL` values; match rates computed strictly over active allotment years; informative counseling advisory displayed. |
| **7.5% Govt School Quota Representation** | Data Schema | Medium | **[RESOLVED]** Source data confirmed General Academic. Backend `resolve_quota` serves baseline cutoffs with explicit DoTE statutory counseling advisory banner. |
| **Institutional Tiering Criteria** | Data Schema | Low | **[RESOLVED]** Implemented in `scripts/classify_tiers.py`. Classified all 467 institutions into Tier-1 (69), Tier-2 (211), and Tier-3 (187) with 0 NULLs based on cutoff profiles. |

---

## 12. Verification & Final Status

The CollegeConnect project engineering plan is **100% implemented, integrated, and verified**.

* **Automated Verification:** Verified by `python scripts/verify_system.py` passing **29 out of 29 tests (100% pass rate)**.
* **Database State:** 467 colleges, 116 branches, 113,218 historical admission records active in MySQL `collegeconnect`.
* **System Status:** Ready for academic demonstration and production deployment.
