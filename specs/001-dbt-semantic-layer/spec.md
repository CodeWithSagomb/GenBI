# Feature Specification : Couche Sémantique dbt

**Feature** : `001-dbt-semantic-layer`
**Créée** : 2026-05-28
**Statut** : Draft
**Priorité** : BLOQUANTE — prérequis de toutes les features suivantes

---

## Contexte Métier

Les pharmacies de Dakar collectent des données brutes (ventes, stocks, approvisionnements) dans une base de données non structurée pour l'analyse. Un pharmacien ne peut pas exploiter ces données sans un analyste. Cette feature crée la couche intermédiaire qui rend les données compréhensibles par un système intelligent.

---

## User Stories & Scénarios de Test

### User Story 1 — Le pharmacien interroge ses ventes du mois (Priorité : P1)

Un pharmacien demande "Quel est mon chiffre d'affaires de ce mois ?" et obtient un chiffre exact, ventilé par mode de paiement (espèces, Wave, Tiers-Payant).

**Pourquoi P1** : C'est la question la plus fréquente dans une officine. Valider cette story prouve que la couche sémantique fonctionne pour le cas d'usage le plus critique.

**Test indépendant** : Peut être validé en exécutant une requête SQL directement sur la table `marts.fct_sales` et en vérifiant que le résultat correspond aux données brutes dans `raw.sales`.

**Scénarios d'acceptance** :
1. **Étant donné** que les données de ventes de Mai 2026 sont dans le système, **Quand** on interroge le CA total de Mai 2026, **Alors** le résultat correspond à la somme de `raw.sales.total_amount_fcfa` pour les dates concernées.
2. **Étant donné** une vente en Tiers-Payant, **Quand** on interroge la répartition espèces/Tiers-Payant, **Alors** les montants `patient_share_fcfa` et `insurer_share_fcfa` sont corrects.
3. **Étant donné** une journée sans ventes (dimanche de garde minimale), **Quand** on interroge ce jour, **Alors** le résultat est 0 FCFA, pas une erreur.

---

### User Story 2 — Le pharmacien identifie ses produits les plus vendus (Priorité : P2)

Un pharmacien peut demander "Quels sont mes 10 produits les plus vendus ce trimestre ?" et obtenir un classement par quantité et par chiffre d'affaires.

**Pourquoi P2** : La gestion des stocks repose sur cette information. C'est la deuxième question la plus demandée après le CA global.

**Test indépendant** : Requête sur `marts.fct_sales` jointe avec `marts.dim_products`, groupée par produit, triée par quantité — résultat vérifiable contre `raw.sale_details`.

**Scénarios d'acceptance** :
1. **Étant donné** 15 produits avec des ventes variables, **Quand** on interroge le top 10 par quantité, **Alors** le classement correspond aux agrégations de `raw.sale_details.quantity`.
2. **Étant donné** un produit générique et son équivalent de marque (ex: Amoxicilline et Augmentin), **Quand** on demande par classe thérapeutique, **Alors** les deux apparaissent sous "Antibiotique".
3. **Étant donné** un produit de parapharmacie (TVA 18%), **Quand** on demande le CA, **Alors** le montant HT et TTC sont distinguables.

---

### User Story 3 — Le pharmacien suit ses alertes de stock critique (Priorité : P3)

Un pharmacien peut demander "Quels médicaments vont expirer dans les 30 prochains jours ?" ou "Quels produits sont sous le seuil de sécurité ?" et obtenir une liste actionnable.

**Pourquoi P3** : La gestion des péremptions est critique mais moins fréquemment interrogée. Dépend de la table `stocks` correctement modélisée.

**Test indépendant** : Requête sur `marts.dim_stocks` filtrant les lots dont `expiration_date < CURRENT_DATE + 30` — vérifiable contre `raw.stocks`.

**Scénarios d'acceptance** :
1. **Étant donné** un lot expirant le 20 Juin 2026 (LOT-B), **Quand** on interroge le 28 Mai 2026, **Alors** ce lot apparaît dans les alertes de péremption à 30 jours.
2. **Étant donné** un stock avec 5 unités et un seuil de sécurité de 10, **Quand** on demande les produits en rupture imminente, **Alors** ce produit apparaît avec son seuil.
3. **Étant donné** un Lovenox (médicament réfrigéré), **Quand** on demande les alertes, **Alors** sa localisation "Frigo Thermostaté 1" est visible.

---

### Cas limites

- Que se passe-t-il si une vente a un `client_id` NULL (client anonyme) ? La requête ne doit pas échouer.
- Que se passe-t-il si un produit n'a jamais été vendu ? Il doit apparaître avec un CA de 0, pas être absent des résultats de dimension.
- Que se passe-t-il si la date demandée est dans le futur ? Le résultat doit être 0 ou vide, pas une erreur.

---

## Exigences Fonctionnelles

- **EF-001** : Le système DOIT exposer une table de faits centrale des ventes avec le grain "une ligne par vente".
- **EF-002** : Le système DOIT exposer des dimensions produits, clients, pharmacies et assureurs séparées.
- **EF-003** : Chaque table et chaque colonne DOIT avoir une description en français lisible par un non-technique.
- **EF-004** : Le système DOIT exécuter des tests de qualité sur toutes les clés primaires (unicité, non-nullité) et clés étrangères (intégrité référentielle).
- **EF-005** : Le système DOIT produire un fichier de métadonnées `manifest.json` consommable par le backend.
- **EF-006** : Les données de ventes manquées (ruptures) et de retours grossistes DOIVENT être exposées comme des tables de faits séparées.
- **EF-007** : Le calcul de la part assureur vs part patient DOIT être précis et testé sur des cas réels de Tiers-Payant.

---

## Entités Clés

- **Vente** : événement transactionnel avec un montant total, une répartition patient/assureur, un mode de paiement, une date, une pharmacie
- **Ligne de vente** : détail produit d'une vente (quantité, prix unitaire)
- **Produit** : médicament ou article de parapharmacie avec sa classe thérapeutique, son origine (local/importé), son statut générique
- **Client** : patient avec son type (passant/assuré) et son statut chronique
- **Stock** : lot physique d'un produit avec sa date de péremption et son emplacement
- **Vente manquée** : demande non servie faute de stock
- **Retour grossiste** : lot renvoyé au fournisseur (péremption proche)

---

## Critères de Succès Mesurables

- **CS-001** : 100% des colonnes des tables `marts` ont une description non-vide dans le YAML dbt.
- **CS-002** : Tous les tests dbt (`dbt test`) passent sans erreur sur le jeu de données généré.
- **CS-003** : Une requête sur "CA du mois de Mars 2026" retourne un résultat identique qu'elle soit exécutée via la table marts ou directement via les tables raw (validation de cohérence).
- **CS-004** : Le fichier `manifest.json` est généré et contient les métadonnées de toutes les tables marts et staging.
- **CS-005** : Un pharmacien non-technique peut lire les descriptions de colonnes dans la documentation dbt et comprendre ce qu'elles représentent.

---

## Hypothèses

- Les données brutes dans `raw.*` sont déjà présentes et correctement peuplées par le DAG Airflow `ingest_pharmacy_data`.
- Le dialecte SQL est PostgreSQL — pas de compatibilité multi-base nécessaire.
- La devise est le Franc CFA (XOF) — les montants sont des entiers stricts, pas de décimaux.
- Les données couvrent 3 pharmacies de Dakar sur la période Mars–Mai 2026.
- dbt-core est installé localement en dehors de Docker (pas de conteneurisation de dbt).
