# Vision, Contexte et Objectifs : Projet GenBI Open-Source & Vendor-Agnostic

Ce document définit la vision stratégique, le contexte technologique, les choix d'architecture et la feuille de route provisoire pour la réalisation de notre plateforme de **Business Intelligence Générative (GenBI)**.

---

## 1. La Vision Stratégique

### Démocratiser l'accès à la donnée sans compromis sur la gouvernance
La vision de ce projet est de construire une plateforme d'analyse de données conversationnelle où **n'importe quel utilisateur peut interroger l'entrepôt de données en langage naturel**, tout en garantissant des réponses mathématiquement exactes, sécurisées et gouvernées par les ingénieurs de données.

### Les 3 Principes Fondateurs :
1. **100% Vendor-Agnostic & Open-Source :** Aucune dépendance vis-à-vis de solutions cloud propriétaires (AWS, Azure, GCP) ou d'outils de BI payants. Le projet est portable et peut s'exécuter localement (Mac/PC) ou sur un serveur privé grâce à Docker.
2. **Sémantique-First (Pas d'IA en roue libre) :** L'IA ne génère pas de requêtes SQL à partir de tables brutes. Elle est guidée par une couche sémantique stricte et documentée fournie par **dbt**, éliminant ainsi 90% des hallucinations classiques.
3. **Sécurité et Contrôle (Guardrails) :** Chaque requête générée par l'IA passe par un validateur syntaxique et sécuritaire avant d'être exécutée sur la base de données de production.

---

## 2. Le Contexte & Les Enjeux

### Le Problème de la BI Traditionnelle
Dans la plupart des organisations, l'accès à la donnée est ralenti par un goulot d'étranglement : les décideurs dépendent des analystes pour créer des dashboards ou écrire des requêtes SQL complexes. Cela crée de la frustration et ralentit la prise de décision.

### Les Limites des Solutions d'IA Simplistes (Text-to-SQL brut)
Envoyer le schéma brut d'une base de données à un LLM en lui demandant d'écrire du SQL échoue systématiquement dans la vraie vie :
* L'IA ne connaît pas les règles métiers (ex: calcul du taux d'attrition client).
* L'IA se trompe sur les jointures de tables complexes.
* L'IA pose des risques de sécurité (injections SQL, suppression de données).

### Notre Solution : L'alliance du Data Engineering et de l'IA Locale
Nous résolvons ces problèmes en couplant un pipeline de données moderne et gouverné avec une IA locale privée :
* **Qualité de la donnée :** dbt structure la donnée brute (`raw`) en modèles nettoyés (`staging`) puis en tables prêtes à l'analyse (`marts`).
* **Zéro fuite de données :** Ollama héberge le LLM localement sur la machine de l'utilisateur. Aucune donnée sensible n'est envoyée à l'extérieur.
* **Consommation automatique des métadonnées :** L'IA apprend le modèle de données en lisant directement le fichier de configuration de dbt (`manifest.json`).

---

## 3. L'Architecture Cible

L'ensemble de la plateforme est conteneurisé et s'articule ainsi :

```mermaid
graph TD
    subgraph Data Platform (Pipeline & Storage)
        Sources[Données API / CSV] -->|Ingestion Airflow| PostgresRaw[(PostgreSQL : Schema RAW)]
        PostgresRaw -->|Transformations & Tests dbt| PostgresStg[(PostgreSQL : Schema STAGING)]
        PostgresStg -->|Modélisation en Étoile dbt| PostgresMarts[(PostgreSQL : Schema MARTS)]
    end

    subgraph Backend API (FastAPI)
        PostgresMarts -->|Manifest.json| Parser[Parser Python de Métadonnées]
        Parser -->|Context Injection| Prompt[Prompt Template]
        Ollama[Ollama : LLM Local] <-->|Text-to-SQL + Raisonnement| API[API FastAPI]
        Prompt --> API
        API -->|Validation Sécuritaire SQLGlot| Executor[Exécuteur SQL Python]
        Executor -->|Exécution| PostgresMarts
    end

    subgraph Frontend App (React + Vite)
        UI[Interface React + Vite] <-->|Requêtes HTTP / REST| API
        UI <-->|Langage Naturel & Visualisations| User[Utilisateur Final]
    end

    subgraph BI Traditionnelle
        PostgresMarts -->|Visualisation standard| Metabase[Metabase]
    end

    style PostgresMarts fill:#f9f,stroke:#333,stroke-width:2px
    style UI fill:#bbf,stroke:#333,stroke-width:2px
    style API fill:#dfd,stroke:#333,stroke-width:2px
```

---

## 4. Plan Provisoire & Objectifs (Feuille de Route)

Le projet sera découpé en 5 phases progressives et modulaires :

### Phase 1 : Initialisation du Socle Infrastructure & Ingestion
* **Objectif :** Mettre en place l'environnement multi-conteneurs local.
* **Livrables :**
  - Fichier `docker-compose.yml` complet (PostgreSQL, Airflow, Metabase, Ollama, Backend FastAPI, Frontend React).
  - Base de données PostgreSQL configurée avec les schémas `raw`, `staging`, `marts`.
  - Un premier DAG Airflow qui extrait un jeu de données e-commerce réaliste et l'ingère dans le schéma `raw`.

### Phase 2 : Modélisation des Données & Couche Sémantique (dbt)
* **Objectif :** Transformer et structurer la donnée brute pour la rendre "compréhensible" par l'IA.
* **Livrables :**
  - Projet dbt-core initialisé et connecté à PostgreSQL.
  - Modèles de `staging` (nettoyage, renommage, typage).
  - Modèles de `marts` (modélisation en étoile : Table de faits ventes, dimensions clients et produits).
  - Documentation exhaustive de chaque table et colonne dans les fichiers `.yml` de dbt.

### Phase 3 : Développement du Backend API (FastAPI, Ollama, Parser dbt)
* **Objectif :** Créer le cerveau du système sous forme d'API REST robuste.
* **Livrables :**
  - Parser Python pour lire `manifest.json` et extraire dynamiquement les métadonnées.
  - Endpoints FastAPI : `/chat` (génération SQL via Ollama), `/execute` (exécution SQL sécurisée via SQLGlot), `/schema` (liste des tables et colonnes disponibles).
  - Intégration d'Ollama local.

### Phase 4 : Interface Utilisateur Premium (React + Vite)
* **Objectif :** Créer une interface utilisateur interactive et ultra-premium.
* **Livrables :**
  - Application React initialisée avec Vite (HTML/CSS personnalisé, design moderne "dark mode/glassmorphism").
  - Interface de chat fluide pour discuter avec la donnée.
  - Composants de visualisation dynamique des résultats (graphiques interactifs Recharts/Chart.js à partir du JSON renvoyé par l'API).
  - Affichage pas à pas : Question -> Raisonnement de l'IA -> SQL Généré -> Tableau de Résultats / Graphique.

### Phase 5 : Optimisations, RAG & Feedback Loop
* **Objectif :** Rendre l'IA plus intelligente au fil du temps.
* **Livrables :**
  - Base vectorielle locale (ChromaDB) pour stocker et récupérer des exemples SQL types (Few-Shot RAG).
  - Module de validation/correction humaine intégré au frontend (l'utilisateur peut corriger une requête SQL défaillante et l'enregistrer dans la base RAG).
  - Finalisation de la documentation globale et guide d'utilisation.
