CREATE TABLE
    IF NOT EXISTS raw_patient_record (
        raw_id BIGSERIAL PRIMARY KEY,
        source_system TEXT NOT NULL,
        source_patient_id TEXT NOT NULL,
        source_file TEXT NOT NULL,
        payload JSONB NOT NULL,
        extracted_at TIMESTAMPTZ NOT NULL DEFAULT NOW (),
        UNIQUE (source_system, source_patient_id)
    );

CREATE TABLE
    IF NOT EXISTS master_patient (
        master_patient_id TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        full_name TEXT NOT NULL,
        birth_date DATE,
        cin TEXT,
        birth_city TEXT,
        address TEXT,
        gender TEXT CHECK (gender IN ('M', 'F', ''))
    );

-- Idempotence : si la table a déjà été créée sans la colonne gender
-- (version antérieure du schéma), on l'ajoute sans erreur au rechargement.
ALTER TABLE master_patient
    ADD COLUMN IF NOT EXISTS gender TEXT CHECK (gender IN ('M', 'F', ''));

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

-- Liste fermée des finalités (alignée sur engine.governance.consent.PURPOSES).
-- Idempotent : on recree la contrainte a chaque rechargement du schema.
-- Si des lignes hors liste existent deja, la contrainte echoue volontairement :
-- il faut les purger explicitement plutot que d'accepter des finalites libres.
ALTER TABLE consent
    DROP CONSTRAINT IF EXISTS consent_purpose_check;

ALTER TABLE consent
    ADD CONSTRAINT consent_purpose_check
    CHECK (purpose IN ('api_access', 'research', 'analytics'));

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
        purpose TEXT,
        refusal_reason TEXT,
        accessed_at TIMESTAMPTZ DEFAULT NOW ()
    );

-- Idempotence : tables d'audit creees avant le tracage du consentement
-- (version anterieure du schema) → on ajoute les colonnes sans erreur.
ALTER TABLE access_audit
    ADD COLUMN IF NOT EXISTS purpose TEXT;

ALTER TABLE access_audit
    ADD COLUMN IF NOT EXISTS refusal_reason TEXT;

-- Historique chiffré des runs ELT (provision/scripts/utils/run_metrics.py).
-- Un run par ligne, jamais écrasé par le suivant ; un run réenregistré est mis
-- à jour (ON CONFLICT). master_count compte les patients maîtres DISTINCTS.
CREATE TABLE
    IF NOT EXISTS pipeline_run (
        run_id TEXT PRIMARY KEY,
        mode TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('running', 'ok', 'failed')),
        started_at TIMESTAMPTZ,
        finished_at TIMESTAMPTZ,
        failed_step TEXT,
        silver_rows INTEGER,
        master_count INTEGER,
        duplicate_count INTEGER,
        exact_count INTEGER,
        probabilistic_count INTEGER,
        duplicate_rate NUMERIC(5, 2),
        gold_event_rows INTEGER,
        gold_consent_rows INTEGER,
        recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW ()
    );

-- Détail par source : lignes réellement extraites, ou sautées (empreinte
-- inchangée), et lignes patient de la source présentes en SILVER.
CREATE TABLE
    IF NOT EXISTS pipeline_run_source (
        run_id TEXT NOT NULL REFERENCES pipeline_run (run_id),
        source_system TEXT NOT NULL,
        tables_extracted INTEGER NOT NULL DEFAULT 0,
        tables_skipped INTEGER NOT NULL DEFAULT 0,
        tables_failed INTEGER NOT NULL DEFAULT 0,
        rows_extracted BIGINT NOT NULL DEFAULT 0,
        rows_skipped BIGINT NOT NULL DEFAULT 0,
        silver_patient_rows INTEGER,
        PRIMARY KEY (run_id, source_system)
    );
