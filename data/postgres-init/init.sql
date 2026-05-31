-- Initialisation PostgreSQL GenBI
-- Exécuté une seule fois au premier démarrage du conteneur

CREATE DATABASE airflow;
CREATE DATABASE genbi;

\c genbi;

-- Schémas (pipeline raw → staging → marts)
CREATE SCHEMA raw;
CREATE SCHEMA staging;
CREATE SCHEMA marts;

-- ── Utilisateurs ────────────────────────────────────────────────────────────

-- genbi_readonly : lecture seule pour l'agent IA (toutes les routes sauf feedback)
CREATE USER genbi_readonly WITH PASSWORD 'genbi_secure_readonly_123' NOBYPASSRLS;
GRANT USAGE ON SCHEMA raw      TO genbi_readonly;
GRANT USAGE ON SCHEMA staging  TO genbi_readonly;
GRANT USAGE ON SCHEMA marts    TO genbi_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw     GRANT SELECT ON TABLES TO genbi_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT SELECT ON TABLES TO genbi_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA marts   GRANT SELECT ON TABLES TO genbi_readonly;

-- genbi_write : INSERT uniquement sur raw.feedback
CREATE USER genbi_write WITH PASSWORD 'genbi_write_456';
GRANT USAGE ON SCHEMA raw TO genbi_write;

-- ── Table users (JWT/RBAC — Phase 5) ────────────────────────────────────────

CREATE TABLE raw.users (
    user_id       SERIAL PRIMARY KEY,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    pharmacy_id   INT,                                        -- NULL pour le rôle admin
    role          VARCHAR(20) CHECK (role IN ('pharmacist', 'admin')) NOT NULL DEFAULT 'pharmacist',
    created_at    TIMESTAMP DEFAULT NOW()
);

-- genbi_readonly peut lire raw.users pour l'authentification JWT
GRANT SELECT ON raw.users TO genbi_readonly;
GRANT USAGE, SELECT ON SEQUENCE raw.users_user_id_seq TO genbi_readonly;

-- Données de test (mot de passe : test123 / admin123 — bcrypt rounds=12)
INSERT INTO raw.users (email, password_hash, pharmacy_id, role) VALUES
    ('bourguiba@pharma.sn', '$2b$12$3Sc8Z.LtO3b6NZtcTgcWbOV5stOderdPythHGrr/DzQvlZX6qfNL.', 1, 'pharmacist'),
    ('almadies@pharma.sn',  '$2b$12$FLIae.00x29ZascdFxGdWOuLOaszXYJfXn72oaTYFa75YbB4ZrMlW', 2, 'pharmacist'),
    ('nation@pharma.sn',    '$2b$12$n6eXGpBHoG6Kq0nMGPwjXO2oYucaBRinCJ/dWUNIfepCeHoNY6BxS', 3, 'pharmacist'),
    ('admin@genbi.sn',      '$2b$12$0psSO3h4w2CZ0l2O5HiwZOqH7FpGZyz5IGX0ekwMoksUISFkc6oHK', NULL, 'admin');

-- ── Table feedback ───────────────────────────────────────────────────────────

CREATE TABLE raw.feedback (
    feedback_id   SERIAL PRIMARY KEY,
    pharmacy_id   INT NOT NULL,
    question      TEXT NOT NULL,
    sql_generated TEXT,
    rating        VARCHAR(4) CHECK (rating IN ('good', 'bad')) NOT NULL,
    comment       TEXT,
    created_at    TIMESTAMP DEFAULT NOW()
);
-- INSERT + SELECT requis : SELECT est nécessaire pour la clause RETURNING
GRANT INSERT, SELECT ON raw.feedback TO genbi_write;
GRANT USAGE, SELECT ON SEQUENCE raw.feedback_feedback_id_seq TO genbi_write;

-- ── Row Level Security ───────────────────────────────────────────────────────
-- Activé après que dbt ait créé les tables marts (via dbt run)
-- Les policies sont appliquées manuellement après la première exécution dbt.
-- Script de référence :
--   ALTER TABLE marts.fct_sales ENABLE ROW LEVEL SECURITY;
--   CREATE POLICY pharmacy_isolation ON marts.fct_sales
--       USING (pharmacy_id = current_setting('app.current_pharmacy_id', true)::int);
-- (répéter pour fct_purchases, fct_missed_sales, fct_wholesaler_returns)

-- ── Sécurité générale ────────────────────────────────────────────────────────
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
