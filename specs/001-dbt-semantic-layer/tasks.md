# Tasks : 001-dbt-semantic-layer

**Input** : `specs/001-dbt-semantic-layer/spec.md`
**Constitution** : `.specify/memory/constitution.md`
**Prérequis** : Données `raw.*` peuplées par le DAG Airflow

---

## Stratégie de test pour dbt

Les tests dbt sont **natifs et obligatoires** — ils s'écrivent dans les fichiers `.yml` en même temps que le modèle SQL, pas après. Chaque modèle créé doit immédiatement avoir :
- `unique` + `not_null` sur la clé primaire
- `relationships` sur chaque clé étrangère
- `accepted_values` sur les colonnes à cardinalité fixe (ex: `payment_method`, `client_type`)

La commande `dbt test` est le critère de validation de chaque checkpoint.

---

## Format : `[ID] [P?] [US?] Description`
- `[P]` = peut s'exécuter en parallèle (fichiers différents, pas de dépendance)
- `[USN]` = appartient à la User Story N
- Chaque tâche = un fichier ou un artefact unique

---

## Phase 1 : Setup (Infrastructure dbt)

**Objectif** : Initialiser le projet dbt et connecter à PostgreSQL.

- [ ] T001 Initialiser dbt-core dans `dbt_project/` avec `dbt init genbi`
- [ ] T002 Configurer `dbt_project/profiles.yml` avec la connexion PostgreSQL locale (host: localhost, port: 5432, db: genbi, user: postgres)
- [ ] T003 [P] Configurer `dbt_project/dbt_project.yml` : nom du projet, chemins des modèles, matérialisations par défaut (staging: view, marts: table)
- [ ] T004 Valider la connexion : `dbt debug` doit retourner "All checks passed"

**Checkpoint** : `dbt debug` passe. La base de données est accessible.

---

## Phase 2 : Sources (Déclaration des tables raw)

**Objectif** : Déclarer les 10 tables `raw.*` comme sources dbt.

- [ ] T005 Créer `dbt_project/models/staging/raw/_raw__sources.yml` avec la déclaration des 10 tables sources :
  - `raw.pharmacies`, `raw.products`, `raw.clients`, `raw.insurers`
  - `raw.stocks`, `raw.purchases`, `raw.sales`, `raw.sale_details`
  - `raw.missed_sales`, `raw.wholesaler_returns`
- [ ] T006 Valider que `dbt source freshness` ou `dbt compile` reconnaît les sources sans erreur

**Checkpoint** : Sources déclarées. dbt compile ne lève aucune erreur sur les sources.

---

## Phase 3 : Staging — User Story 1 & 2 (Ventes & Produits) 🎯 MVP

**Objectif** : Nettoyer et normaliser les données brutes de ventes et de produits.

### Implémentation Staging US1 & US2

- [ ] T007 [P] [US1] Créer `models/staging/raw/stg_raw__sales.sql` : renommer colonnes, caster les types, ajouter `sale_date::date`
- [ ] T008 [P] [US2] Créer `models/staging/raw/stg_raw__sale_details.sql` : renommer, caster
- [ ] T009 [P] [US2] Créer `models/staging/raw/stg_raw__products.sql` : renommer, normaliser `is_generic`, `is_regulated`, `origin`
- [ ] T010 [P] Créer `models/staging/raw/stg_raw__clients.sql`
- [ ] T011 [P] Créer `models/staging/raw/stg_raw__pharmacies.sql`
- [ ] T012 [P] Créer `models/staging/raw/stg_raw__insurers.sql`
- [ ] T013 Créer `models/staging/raw/_raw__models.yml` avec description de CHAQUE colonne pour les 6 modèles staging ci-dessus (constitution EF-003)
- [ ] T014 Dans `_raw__models.yml` — ajouter les tests par colonne :
  - `unique` + `not_null` sur tous les `*_id`
  - `accepted_values` : `client_type` → ['Passant','Assuré'], `payment_method` → ['Espèces','Wave','Orange Money','Tiers-Payant']
  - `relationships` : `stg_raw__sales.pharmacy_id` → `stg_raw__pharmacies.pharmacy_id`
  - `relationships` : `stg_raw__sales.insurer_id` → `stg_raw__insurers.insurer_id`
  - `not_null` : `total_amount_fcfa`, `sale_date`
- [ ] T015 Exécuter `dbt run --select staging` puis `dbt test --select staging` — 0 échec attendu

**Checkpoint US1 & US2** : `dbt test` passe pour les modèles staging ventes/produits. La vue `staging.stg_raw__sales` est requêtable.

---

## Phase 4 : Staging — User Story 3 (Stocks & Opérations)

- [ ] T016 [P] [US3] Créer `models/staging/raw/stg_raw__stocks.sql`
- [ ] T017 [P] Créer `models/staging/raw/stg_raw__purchases.sql`
- [ ] T018 [P] Créer `models/staging/raw/stg_raw__missed_sales.sql`
- [ ] T019 [P] Créer `models/staging/raw/stg_raw__wholesaler_returns.sql`
- [ ] T020 Compléter `_raw__models.yml` — descriptions + tests pour les 4 nouveaux modèles :
  - `stocks` : `not_null` sur `quantity_in_stock`, `expiration_date` ; `relationships` vers `products`
  - `purchases` : `accepted_values` sur taux de livraison ; `relationships` vers `pharmacies` et `products`
  - `missed_sales` : `not_null` sur `missed_date`, `requested_quantity > 0`
  - `wholesaler_returns` : `accepted_values` sur `status` → ['Validé','En attente']
- [ ] T021 Exécuter `dbt run --select staging` puis `dbt test --select staging` — 10 modèles, 0 échec

**Checkpoint US3** : Tous les 10 modèles staging sont verts. `dbt test` passe à 100%.

---

## Phase 5 : Marts — Dimensions

**Objectif** : Créer les tables de dimension stables (faible cardinalité, peu de changements).

- [ ] T022 [P] Créer `models/marts/pharmacy/dim_products.sql` : large et dénormalisé (classe thérapeutique, DCI, forme, laboratoire, origine, is_generic, prix public)
- [ ] T023 [P] Créer `models/marts/pharmacy/dim_clients.sql` : type client, statut chronique, points fidélité
- [ ] T024 [P] Créer `models/marts/pharmacy/dim_pharmacies.sql`
- [ ] T025 [P] Créer `models/marts/pharmacy/dim_insurers.sql`
- [ ] T026 Créer `models/marts/pharmacy/_pharmacy__models.yml` — description CHAQUE colonne (français, niveau pharmacien) + tests :
  - `unique` + `not_null` sur `product_id`, `client_id`, `pharmacy_id`, `insurer_id`
  - `accepted_values` : `origin` → ['Importé','Local'] ; `is_generic` → [true, false]

**Checkpoint Dimensions** : Les 4 tables `dim_*` sont créées et documentées.

---

## Phase 6 : Marts — Tables de Faits 🎯 Livrable Principal

**Objectif** : Créer les tables de faits analytiques principales.

- [ ] T027 [US1] [US2] Créer `models/marts/pharmacy/fct_sales.sql` :
  - Grain : une ligne par vente (`sale_id`)
  - Jointures : avec `stg_raw__sale_details` pour le calcul de métriques agrégées
  - Colonnes : `sale_id`, `pharmacy_id`, `client_id`, `sale_date`, `payment_method`, `client_type`, `insurer_id`, `total_amount_fcfa`, `patient_share_fcfa`, `insurer_share_fcfa`, `vat_amount_fcfa`, `nb_products_in_cart`
- [ ] T028 [US3] Créer `models/marts/pharmacy/fct_missed_sales.sql` : grain = une ligne par rupture
- [ ] T029 Créer `models/marts/pharmacy/fct_purchases.sql` : grain = une ligne par commande grossiste
- [ ] T030 Créer `models/marts/pharmacy/fct_wholesaler_returns.sql`
- [ ] T031 [US3] Créer `models/marts/pharmacy/dim_stocks.sql` : état actuel du stock avec alertes de péremption calculées
- [ ] T032 Compléter `_pharmacy__models.yml` pour les tables de faits — description + tests :
  - `fct_sales` : `unique` + `not_null` sur `sale_id` ; `not_null` sur `total_amount_fcfa`, `sale_date` ; `accepted_values` sur `payment_method` et `client_type`
  - `fct_sales` : test custom — `patient_share_fcfa + insurer_share_fcfa = total_amount_fcfa` (cohérence tiers-payant)
  - `fct_purchases` : `not_null` sur `quantity_ordered` ; test `quantity_received <= quantity_ordered`
  - `fct_missed_sales` : `not_null` sur `missed_date`, `requested_quantity`
  - `dim_stocks` : `not_null` sur `expiration_date`, `quantity_in_stock`
- [ ] T033 Ajouter tests `relationships` entre faits et dimensions dans `_pharmacy__models.yml` :
  - `fct_sales.pharmacy_id` → `dim_pharmacies.pharmacy_id`
  - `fct_sales.product_id` (via sale_details) → `dim_products.product_id`
  - `fct_sales.insurer_id` → `dim_insurers.insurer_id`
- [ ] T034 Exécuter `dbt run` complet puis `dbt test` — cible : **0 échec sur l'ensemble des modèles**

**Checkpoint Faits** : Toutes les tables `fct_*` et `dim_*` sont requêtables. `dbt test` est vert à 100%.

---

## Phase 7 : Génération du Manifest & Validation Finale

**Objectif** : Produire les artefacts consommés par le backend.

- [ ] T035 Exécuter `dbt docs generate` pour produire `target/manifest.json` et `target/catalog.json`
- [ ] T036 Valider que `target/manifest.json` contient les descriptions de colonnes pour tous les modèles marts (vérification manuelle d'un échantillon de 3 tables)
- [ ] T037 [CS-003] Valider la cohérence des données : exécuter une requête sur `marts.fct_sales` et comparer avec `raw.sales` pour le CA de Mars 2026
- [ ] T038 [CS-005] Valider la lisibilité : faire lire les descriptions de colonnes par un non-technique et confirmer qu'elles sont compréhensibles
- [ ] T039 Exécuter `dbt docs serve` et vérifier la documentation dans le navigateur

**Checkpoint Final** : `manifest.json` généré, tests 100% verts, cohérence des données validée.

---

## Dépendances & Ordre d'exécution

```
Phase 1 (Setup)
    ↓
Phase 2 (Sources)
    ↓
Phase 3 & 4 (Staging — parallélisables entre eux)
    ↓
Phase 5 (Dimensions — dépend du staging)
    ↓
Phase 6 (Faits — dépend des dimensions et du staging)
    ↓
Phase 7 (Validation finale)
```

Les tâches marquées `[P]` dans la même phase peuvent être développées en parallèle.

---

## Opportunités de parallélisme

```bash
# Phase 3 : tous ces fichiers peuvent être créés simultanément
T007 stg_raw__sales.sql
T008 stg_raw__sale_details.sql
T009 stg_raw__products.sql
T010 stg_raw__clients.sql
T011 stg_raw__pharmacies.sql
T012 stg_raw__insurers.sql

# Phase 5 : toutes les dimensions en parallèle
T022 dim_products.sql
T023 dim_clients.sql
T024 dim_pharmacies.sql
T025 dim_insurers.sql
```

---

## Stratégie MVP

**MVP minimal (User Story 1 uniquement) :**
1. Phase 1 + 2 (Setup)
2. T007 (`stg_raw__sales.sql`) + T011 (`stg_raw__pharmacies.sql`)
3. T027 (`fct_sales.sql`) avec jointure minimale
4. T035 (`dbt docs generate`)
5. **ARRÊTER et valider** : une requête "CA du mois" fonctionne → passer au backend

**Livraison complète :** Phases 1 à 7 dans l'ordre.
