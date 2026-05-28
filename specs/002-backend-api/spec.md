# Feature Specification : API Backend GenBI

**Feature** : `002-backend-api`
**Créée** : 2026-05-28
**Statut** : Draft
**Dépend de** : `001-dbt-semantic-layer` (manifest.json requis)

---

## Contexte Métier

Un pharmacien pose une question en français. Un système intelligent comprend la question, interroge les données de la pharmacie, et renvoie une réponse compréhensible avec le détail du raisonnement. Tout se passe localement — aucune donnée ne quitte le réseau.

---

## User Stories & Scénarios de Test

### User Story 1 — Le pharmacien pose une question et reçoit une réponse (Priorité : P1)

Un pharmacien tape "Quel est mon CA du mois de Mai 2026 ?" et reçoit en retour : le montant total, la répartition par mode de paiement, et le SQL généré (pour la transparence).

**Pourquoi P1** : C'est le cas d'usage central de GenBI. Tout le reste en découle.

**Test indépendant** : Envoyer un POST sur `/api/v1/chat` avec une question simple → vérifier que le JSON retourné contient un champ `sql` valide et un champ `question` reflétant la question posée.

**Scénarios d'acceptance** :
1. **Étant donné** une question sur le CA, **Quand** le backend reçoit la requête, **Alors** il retourne un SQL SELECT valide ciblant `marts.fct_sales`.
2. **Étant donné** une question ambiguë, **Quand** le LLM ne peut pas générer de SQL fiable, **Alors** le backend retourne un message d'erreur clair en français, pas une stack trace.
3. **Étant donné** une question dans un domaine non couvert (ex: "Donne-moi le mot de passe admin"), **Alors** le backend refuse poliment et explique ce qu'il peut faire.

---

### User Story 2 — Le SQL généré est exécuté de façon sécurisée (Priorité : P1)

Le SQL généré par l'IA est validé, exécuté sur la base de données en lecture seule, et les résultats sont retournés en JSON structuré.

**Pourquoi P1** : Sans exécution sécurisée, la génération SQL n'a aucune valeur. Ces deux stories forment le cœur du système.

**Test indépendant** : Envoyer un POST sur `/api/v1/execute` avec un SQL SELECT valide → recevoir des données JSON. Envoyer un DELETE → recevoir une erreur 400.

**Scénarios d'acceptance** :
1. **Étant donné** un SQL `SELECT SUM(total_amount_fcfa) FROM marts.fct_sales`, **Quand** exécuté, **Alors** le résultat est un JSON avec les colonnes et les lignes.
2. **Étant donné** un SQL `DELETE FROM marts.fct_sales`, **Quand** soumis, **Alors** le backend retourne une erreur 400 avec le message "Opération interdite : seules les requêtes SELECT sont autorisées."
3. **Étant donné** un SQL avec une syntaxe invalide, **Quand** soumis, **Alors** le backend retourne une erreur 400 avec le détail de l'erreur de parsing.

---

### User Story 3 — Le frontend peut découvrir le schéma disponible (Priorité : P2)

L'interface peut interroger la liste des tables et colonnes disponibles pour contextualiser les questions de l'utilisateur.

**Pourquoi P2** : Permet au frontend d'afficher des suggestions et d'améliorer l'expérience, mais n'est pas bloquant pour le MVP.

**Test indépendant** : Appel GET `/api/v1/schema` → liste structurée des tables marts et leurs colonnes avec descriptions.

---

## Exigences Fonctionnelles

- **EF-001** : `POST /api/v1/chat` DOIT recevoir une question en texte libre et retourner le SQL généré + la question reformulée.
- **EF-002** : `POST /api/v1/execute` DOIT recevoir un SQL, le valider, l'exécuter en lecture seule, et retourner les résultats en JSON.
- **EF-003** : `GET /api/v1/schema` DOIT retourner la liste des tables disponibles avec leurs descriptions extraites du manifest.json.
- **EF-004** : Tout SQL contenant une instruction non-SELECT DOIT être rejeté avec un code HTTP 400 avant exécution.
- **EF-005** : La connexion à la base de données pour l'exécution DOIT utiliser l'utilisateur `genbi_readonly` uniquement.
- **EF-006** : Le contexte injecté dans le prompt DOIT provenir exclusivement du `manifest.json` dbt — jamais du schéma brut PostgreSQL.
- **EF-007** : L'API DOIT retourner une réponse HTTP en moins de 30 secondes, avec un timeout explicite si le LLM ne répond pas.
- **EF-008** : `GET /api/health` DOIT retourner le statut de connectivité : base de données accessible, Ollama accessible, manifest.json chargé.

---

## Critères de Succès Mesurables

- **CS-001** : 80% des questions sur les ventes (CA, top produits, comparaisons de périodes) produisent un SQL exécutable du premier coup.
- **CS-002** : 100% des tentatives d'injection SQL (DELETE, DROP, INSERT) sont rejetées avant exécution.
- **CS-003** : `GET /api/health` retourne un statut "healthy" quand tous les services sont opérationnels.
- **CS-004** : La réponse à une question simple arrive en moins de 15 secondes sur le matériel cible (MacBook avec Ollama natif).
- **CS-005** : Zéro données écrites en base de données via l'API — vérifiable par audit des logs PostgreSQL.

---

## Hypothèses

- `dbt docs generate` a été exécuté et `manifest.json` est présent dans `dbt_project/target/`.
- Ollama est installé nativement sur macOS et le modèle `qwen2.5-coder:7b` est téléchargé.
- Le backend tourne dans Docker mais accède à Ollama via `host.docker.internal:11434`.
- La base de données PostgreSQL est accessible sur `postgres:5432` depuis le conteneur Docker.
- L'utilisateur `genbi_readonly` existe avec les droits SELECT sur les schémas staging et marts.
