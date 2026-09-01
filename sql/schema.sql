CREATE TABLE
    raw_patient_record (
        raw_id BIGSERIAL PRIMARY KEY,
        source_system TEXT NOT NULL,
        source_patient_id TEXT NOT NULL,
        source_file TEXT NOT NULL,
        payload JSONB NOT NULL,
        extracted_at TIMESTAMPTZ NOT NULL DEFAULT NOW ()
    );

CREATE TABLE
    master_patient (
        master_patient_id TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        full_name TEXT NOT NULL,
        birth_date DATE,
        phone TEXT,
        address TEXT
    );

CREATE TABLE
    patient_identity_map (
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
    consent (
        consent_id BIGSERIAL PRIMARY KEY,
        master_patient_id TEXT NOT NULL REFERENCES master_patient (master_patient_id),
        purpose TEXT NOT NULL,
        granted BOOLEAN NOT NULL,
        recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW ()
    );