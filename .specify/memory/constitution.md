# GenBI Constitution

## Principe I — Souveraineté des Données (NON-NÉGOCIABLE)

Aucune donnée de patient, de transaction ou de stock ne doit quitter le réseau local de la pharmacie. Le LLM doit s'exécuter localement sur le matériel de l'utilisateur. Toute dépendance vers un service cloud externe (OpenAI, AWS, Azure) pour le traitement des données est interdite. Les APIs cloud ne sont autorisées que pour des métadonnées non-sensibles (ex : téléchargement de modèles).

**Rationale** : Les données pharmaceutiques sont soumises au secret médical et aux réglementations locales (Sénégal, UEMOA). Une fuite constitue un risque légal et éthique majeur.

## Principe II — Sémantique-First (NON-NÉGOCIABLE)

L'IA ne génère jamais de SQL à partir du schéma brut des tables de la base de données. Toute génération de requête DOIT s'appuyer sur les métadonnées documentées dans le `manifest.json` de dbt — incluant les descriptions de tables, les descriptions de colonnes, et les relations entre modèles. Un endpoint de génération SQL sans manifest.json valide DOIT échouer explicitement avec une erreur compréhensible.

**Rationale** : Le texte-vers-SQL brut produit des hallucinations sur les jointures et les règles métier. La couche sémantique dbt réduit le taux d'erreur de ~60% à ~5%.

## Principe III — Sécurité par Architecture (NON-NÉGOCIABLE)

L'agent IA DOIT utiliser exclusivement un utilisateur PostgreSQL en lecture seule (`genbi_readonly`) pour toutes ses connexions à la base de données. L'utilisateur administrateur (`postgres`) ne doit jamais être utilisé dans le code du backend ou du frontend. Toute requête SQL générée DOIT être parsée avant exécution pour rejeter toute instruction non-SELECT (INSERT, UPDATE, DELETE, DROP, CREATE, TRUNCATE). Les paramètres SQL DOIVENT être passés via des requêtes paramétrées, jamais interpolés dans des strings.

**Rationale** : L'IA peut produire des requêtes destructives par erreur. L'architecture zero-trust garantit qu'une hallucination ne peut pas corrompre les données.

## Principe IV — Open-Source & Vendor-Agnostic

Toute dépendance vis-à-vis d'un service cloud payant ou propriétaire est interdite dans l'architecture core. Le projet DOIT pouvoir s'exécuter intégralement sur un serveur local ou un ordinateur personnel sans connexion internet après initialisation. Les outils choisis DOIVENT avoir une licence compatible avec un usage commercial (MIT, Apache 2.0, PostgreSQL).

**Rationale** : Les pharmacies en Afrique de l'Ouest ont des contraintes de connectivité et de budget. La souveraineté technologique est une valeur fondamentale.

## Principe V — Simplicité Incrémentale

Chaque feature DOIT être livrée sous forme de User Stories indépendamment testables et déployables. Aucune User Story ne peut dépendre d'une autre pour être démontrée. La complexité (agents multi-étapes, RAG, orchestration avancée) n'est ajoutée que lorsque la version simple a prouvé ses limites. Le YAGNI (You Ain't Gonna Need It) s'applique à toutes les décisions d'architecture.

**Rationale** : Un MVP livrable à chaque étape permet de valider la valeur avec les utilisateurs avant d'investir dans la complexité.

## Contraintes Techniques

- **Dialecte SQL** : PostgreSQL uniquement. Aucune requête générique "standard SQL".
- **Modèle LLM** : Ollama local (`qwen2.5-coder:7b` par défaut). Migrable vers d'autres modèles locaux sans modification de l'architecture.
- **Pipeline de données** : Le schéma raw ne doit jamais être exposé directement à l'IA — uniquement staging et marts.
- **Tests dbt** : Toute colonne clé primaire DOIT avoir les tests `unique` et `not_null`. Toute FK DOIT avoir un test `relationships`.

## Gouvernance

La constitution est la référence unique pour toutes les décisions d'architecture et de code. Tout code qui viole un Principe NON-NÉGOCIABLE doit être refusé en code review, quelle que soit la raison métier invoquée.

Les amendements à la constitution DOIVENT documenter : la raison du changement, les artéfacts impactés, et la procédure de migration. La version est incrémentée selon les règles sémantiques : MAJOR pour les violations rétrospectives, MINOR pour les additions, PATCH pour les clarifications.

**Version** : 1.0.0 | **Ratifiée** : 2026-05-28 | **Dernière modification** : 2026-05-28
