-- script d'initialisation de la base de données PostgreSQL
-- exécuté automatiquement au démarrage du conteneur

-- Création des bases de données de travail
CREATE DATABASE airflow;
CREATE DATABASE genbi;

-- Connexion à la base analytique genbi pour configurer les schémas et la sécurité
\c genbi;

-- Création des schémas d'entrepôt de données (Modèle raw -> staging -> marts)
CREATE SCHEMA raw;
CREATE SCHEMA staging;
CREATE SCHEMA marts;

-- Création de l'utilisateur restreint en lecture seule pour l'Agent IA GenBI (Zero-Trust)
CREATE USER genbi_readonly WITH PASSWORD 'genbi_secure_readonly_123';

-- Attribution des droits d'utilisation des schémas
GRANT USAGE ON SCHEMA raw TO genbi_readonly;
GRANT USAGE ON SCHEMA staging TO genbi_readonly;
GRANT USAGE ON SCHEMA marts TO genbi_readonly;

-- Configuration des droits par défaut pour les futures tables (crucial car dbt ne les a pas encore créées)
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT SELECT ON TABLES TO genbi_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT SELECT ON TABLES TO genbi_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA marts GRANT SELECT ON TABLES TO genbi_readonly;

-- Rendre la sécurité plus explicite en révoquant les droits d'écriture sur le schéma public par défaut
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
