CREATE TABLE
    IF NOT EXISTS raw_patient_record (
        raw_id BIGSERIAL PRIMARY KEY,
        source_system TEXT NOT NULL,
        source_patient_id TEXT NOT NULL,
        source_file TEXT NOT NULL,
        payload JSONB NOT NULL,
        extracted_at TIMESTAMPTZ NOT NULL DEFAULT NOW ()
    );

CREATE TABLE
    IF NOT EXISTS master_patient (
        master_patient_id TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        full_name TEXT NOT NULL,
        birth_date DATE,
        phone TEXT,
        address TEXT
    );

CREATE TABLE
    IF NOT EXISTS patient_identity_map (
        identity_map_id BIGSERIAL PRIMARY KEY,
        master_patient_id TEXT NOT NULL REFERENCES master_patient (master_patient_id),
        source_system TEXT NOT NULL,
        source_patient_id TEXT NOT NULL,
        match_method TEXT NOT NULL CHECK (
            match_method IN ('new_master', 'exact', 'probabilistic')
        ),
        match_score NUMERIC(4, 3) NOT NULL CHECK (
            match_score >= 0
            AND match_score <= 1
        ),
        explanation TEXT NOT NULL,
        matched_at TIMESTAMPTZ NOT NULL DEFAULT NOW (),
        UNIQUE (source_system, source_patient_id)
    );

CREATE TABLE
    IF NOT EXISTS consent (
        consent_id BIGSERIAL PRIMARY KEY,
        master_patient_id TEXT NOT NULL REFERENCES master_patient (master_patient_id),
        purpose TEXT NOT NULL,
        granted BOOLEAN NOT NULL,
        recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW ()
    );

CREATE TABLE
    IF NOT EXISTS medicine_purchase (
        purchase_id BIGSERIAL PRIMARY KEY,
        source_record_id TEXT NOT NULL,
        master_patient_id TEXT NOT NULL REFERENCES master_patient (master_patient_id),
        source_system TEXT NOT NULL,
        source_patient_id TEXT NOT NULL,
        payload JSONB NOT NULL,
        UNIQUE (source_system, source_record_id)
    );

CREATE TABLE
    IF NOT EXISTS patient_consultation (
        consultation_id BIGSERIAL PRIMARY KEY,
        source_record_id TEXT NOT NULL,
        master_patient_id TEXT NOT NULL REFERENCES master_patient (master_patient_id),
        source_system TEXT NOT NULL,
        source_patient_id TEXT NOT NULL,
        payload JSONB NOT NULL,
        UNIQUE (source_system, source_record_id)
    );

CREATE TABLE
    IF NOT EXISTS imaging_exam (
        exam_id BIGSERIAL PRIMARY KEY,
        source_record_id TEXT NOT NULL,
        master_patient_id TEXT NOT NULL REFERENCES master_patient (master_patient_id),
        source_system TEXT NOT NULL,
        source_patient_id TEXT NOT NULL,
        payload JSONB NOT NULL,
        UNIQUE (source_system, source_record_id)
    );

CREATE TABLE
    IF NOT EXISTS api_user (
        user_id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        api_key_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('admin', 'analyst', 'viewer')),
        active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT NOW ()
    );

CREATE TABLE
    IF NOT EXISTS access_audit (
        audit_id BIGSERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES api_user (user_id),
        username TEXT NOT NULL,
        endpoint TEXT NOT NULL,
        method TEXT NOT NULL,
        response_status INTEGER,
        ip_address TEXT,
        accessed_at TIMESTAMPTZ DEFAULT NOW ()
    );