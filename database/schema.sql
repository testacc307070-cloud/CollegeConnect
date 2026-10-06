-- ==============================================================================
-- CollegeConnect - Database Schema Definition
-- Target RDBMS: MySQL 8.4
-- Storage Engine: InnoDB | Character Set: utf8mb4 | Collation: utf8mb4_unicode_ci
-- Normalized Architecture: 3NF / Tall (Unpivoted) Fact Table
-- Reference Specification: DATABASE_SCHEMA.md
-- ==============================================================================

-- 1. Database Initialization
CREATE DATABASE IF NOT EXISTS collegeconnect
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE collegeconnect;

-- ==============================================================================
-- Table: colleges
-- Description: Master dimension table storing canonical institutional profiles
--              for recognized engineering colleges across Tamil Nadu.
-- Normalized: Eliminates 16,000+ redundant text occurrences down to 467 unique rows.
-- ==============================================================================
CREATE TABLE IF NOT EXISTS colleges (
    college_code        INT UNSIGNED NOT NULL COMMENT 'Official 4-digit DoTE counseling code (e.g., 1 to 5990)',
    college_name        VARCHAR(255) NOT NULL COMMENT 'Canonical full institution title',
    district            VARCHAR(50)  NOT NULL COMMENT 'Revenue district of institution (e.g., CHENNAI, COIMBATORE)',
    college_type        VARCHAR(100) NOT NULL COMMENT 'Institutional governance category (e.g., CEG DEPTS, GOVERNMENT ENGG COLLEGES, etc.)',
    institutional_tier  VARCHAR(20)  DEFAULT NULL COMMENT 'Standardized institutional tier (Tier-1, Tier-2, Tier-3) - nullable',
    created_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
    updated_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Automatic row update timestamp',

    -- Primary Key: Direct clustered B-Tree index for O(1) point lookups by college code
    PRIMARY KEY (college_code),

    -- Indexes for Search & Filter Acceleration:
    -- High-selectivity index for instantaneous geographic filtering across TN districts
    INDEX idx_colleges_district (district),
    -- Index supporting administrative filtering by institution type
    INDEX idx_colleges_type (college_type),
    -- Index supporting candidate filtering by institutional ranking tier
    INDEX idx_colleges_tier (institutional_tier),
    -- Prefix B-Tree index for autocomplete and exact institutional title lookups
    INDEX idx_colleges_name (college_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Master dimensional table for Tamil Nadu engineering institutions';

-- ==============================================================================
-- Table: branches
-- Description: Master dimension table storing canonical degree disciplines
--              and academic programs recognized by Anna University and DoTE.
-- Normalized: Eliminates repetitive branch titles down to 116 unique disciplines.
-- ==============================================================================
CREATE TABLE IF NOT EXISTS branches (
    branch_code VARCHAR(10)  NOT NULL COMMENT 'Official DoTE branch/discipline code (e.g., CS, EC, ME, IT, AD)',
    branch_name VARCHAR(255) NOT NULL COMMENT 'Canonical full branch name in Title Case',
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
    updated_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Automatic row update timestamp',

    -- Primary Key: Clustered B-Tree index for instantaneous branch point lookups
    PRIMARY KEY (branch_code),

    -- Index for dropdown generation, sorting, and branch title lookups
    INDEX idx_branches_name (branch_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Master dimensional table for academic engineering disciplines';

-- ==============================================================================
-- Table: historical_admissions
-- Description: Central normalized tall fact table. Every row represents an atomic
--              admission cutoff mark and closing rank for a specific college,
--              branch, academic year, reservation community, and quota.
-- NULL Semantics: Unallotted categories maintain explicit SQL NULL values to protect
--                 averages, percentiles, and historical match-rate calculations.
-- Quota Guardrail: Quota is strictly 'GENERAL' for historical 2021-2025 records.
--                  No unverified 7.5% or special quota records are fabricated.
-- ==============================================================================
CREATE TABLE IF NOT EXISTS historical_admissions (
    record_id     BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Surrogate primary key for API routing and entity identity',
    college_code  INT UNSIGNED    NOT NULL COMMENT 'Foreign key referencing colleges(college_code)',
    branch_code   VARCHAR(10)     NOT NULL COMMENT 'Foreign key referencing branches(branch_code)',
    year          SMALLINT UNSIGNED NOT NULL COMMENT 'Academic admission year (2021-2025)',
    community     ENUM('OC','BC','BCM','MBC','SC','SCA','ST') NOT NULL COMMENT 'Official Tamil Nadu communal reservation category',
    quota         VARCHAR(50)     NOT NULL DEFAULT 'GENERAL' COMMENT 'Counseling quota type (strictly GENERAL for 2021-2025 dataset)',
    cutoff_mark   DECIMAL(6,3)    DEFAULT NULL COMMENT 'Official DoTE closing cutoff aggregate out of 200.000 (NULL if unallotted)',
    closing_rank  INT UNSIGNED    DEFAULT NULL COMMENT 'Official DoTE state overall closing rank (NULL if unallotted)',
    is_partial    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT 'Audit flag: 1 if allotment from partial/supplementary round, 0 otherwise',
    created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Record ingestion timestamp',

    -- Primary Key: Unique surrogate identifier
    PRIMARY KEY (record_id),

    -- Unique Constraint: Guarantees relational uniqueness for each college-branch-year-community-quota tuple
    CONSTRAINT uq_historical_slot UNIQUE KEY (college_code, branch_code, year, community, quota),

    -- Referential Integrity Constraints:
    -- ON UPDATE CASCADE ensures code reassignments propagate automatically
    -- ON DELETE RESTRICT prevents accidental deletion of colleges or branches with historical dependencies
    CONSTRAINT fk_admissions_college FOREIGN KEY (college_code)
        REFERENCES colleges (college_code)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_admissions_branch FOREIGN KEY (branch_code)
        REFERENCES branches (branch_code)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    -- Multi-column composite B-Tree indexes for common candidate filtering and search:
    -- 1. Cutoff-Based Opportunity Search (Matching candidates with Cutoff >= Past Cutoff)
    INDEX idx_comm_quota_year_cutoff (community, quota, year, cutoff_mark),

    -- 2. State Rank-Based Opportunity Search (Matching candidates with Rank <= Closing Rank)
    INDEX idx_comm_quota_year_rank (community, quota, year, closing_rank),

    -- 3. Discipline-Specific Filtering across all institutions for a given academic year
    INDEX idx_branch_year (branch_code, year),

    -- 4. Fast multi-year time-series aggregations and ETL verification
    INDEX idx_year_lookup (year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tall normalized fact table for historical TNEA admission cutoffs and closing ranks';
