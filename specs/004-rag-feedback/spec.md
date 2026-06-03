# Spécification — Phase 5 : RAG + Feedback Loop + JWT/RBAC

**Feature** : `004-rag-feedback`
**Créée** : 2026-05-28
**Mise à jour** : 2026-05-31
**Statut** : Actif
**Dépend de** : `003-frontend-chat` ✅ terminée

---

## Objectif

Transformer GenBI d'un outil de requête one-shot en un système apprenant :
- **Le LLM s'améliore** à chaque validation grâce au RAG (few-shot dynamique)
- **L'utilisateur voit sa conversation** (historique de la session)
- **L'accès est sécurisé** par JWT (plus d'API keys hardcodées)

---

## Architecture Cible Phase 5

```
Navigateur (React)
  │  Authorization: Bearer <jwt>
  ▼
FastAPI
  ├── POST /api/v1/auth/login      ← email + password → JWT
  ├── POST /api/v1/auth/refresh    ← JWT → nouveau JWT
  │
  ├── POST /api/v1/chat            ← question → SQL (enrichi RAG)
  │     │
  │     ├── core/rag.py            ← retrieve top-3 exemples similaires
  │     │     └── ChromaDB PersistentClient (/data/chromadb)
  │     │           └── nomic-embed-text (Ollama natif macOS)
  │     │
  │     └── core/llm.py            ← prompt SQL + exemples few-shot
  │
  ├── POST /api/v1/feedback        ← rating good/bad
  │     └── si good → core/rag.py.index(question, sql)
  │
  └── (tous les autres endpoints inchangés)
```

---

## Trois Tracks Indépendants

### Track 1 — UX Conversation (frontend uniquement)

**Priorité : P1 — À faire en premier**

L'interface passe d'un affichage one-shot à une conversation multi-tours.

#### État actuel
```
useChat state : { status, question, sql, columns, rows, insight, error }
ChatWindow    : affiche 1 seule réponse
```

#### État cible
```
useChat state : {
  messages: [
    { id, role: 'user', content: 'Quel est mon CA ?' },
    { id, role: 'ai', sql, columns, rows, insight, error, feedback: null }
  ],
  status: 'idle' | 'loading' | 'error'
}
ChatWindow : boucle sur messages[], scroll automatique
```

#### Composant FeedbackButtons
- 👍 (`good`) et 👎 (`bad`) sur chaque réponse IA
- Désactivés après un vote (un seul vote par réponse)
- Appel à `chatApi.sendFeedback(question, sql, rating)`
- Confirmation visuelle (couleur + texte "Merci pour votre retour")

#### Règle — Option A validée
L'historique est en mémoire navigateur. Il est perdu au refresh. La persistance cross-session est Phase 6.

---

### Track 2 — RAG ChromaDB

**Priorité : P1 — À faire en deuxième**

Le LLM reçoit des exemples de requêtes similaires déjà validées avant de générer le SQL.

#### Flux complet
```
1. Question : "Quel est mon CA du mois de mars 2026 ?"
2. RAG retrieve : cherche les 3 Q→SQL les plus proches dans ChromaDB
   (filtre : pharmacy_id = 1, collection = "sql_examples")
3. Exemples trouvés (si existants) :
   - "Quel est mon CA de février 2026 ?" → "SELECT SUM(...) WHERE sale_month=2..."
   - "CA total avril ?" → "SELECT SUM(...) WHERE sale_month=4..."
4. Prompt enrichi :
   <examples>
   Question: Quel est mon CA de février 2026 ?
   SQL: SELECT SUM(total_amount_fcfa) FROM marts.fct_sales WHERE sale_month=2...
   </examples>
   <question>Quel est mon CA du mois de mars 2026 ?</question>
5. LLM génère un meilleur SQL grâce aux exemples
6. Utilisateur valide → 👍 → index(question, sql) dans ChromaDB
```

#### Modèle de stockage ChromaDB
```
Collection : "sql_examples_{pharmacy_id}"  ← une collection par pharmacie (isolation)
Document   : question (texte brut)
Embedding  : nomic-embed-text via Ollama
Métadonnées: { pharmacy_id, sql, created_at }
```

#### Infrastructure
- **Mode** : `PersistentClient(path="/data/chromadb")` — pas de service Docker supplémentaire
- **Volume** : bind-mount `./data/chromadb:/data/chromadb` dans `docker-compose.yml`
- **Embedding** : `nomic-embed-text` via LiteLLM (cohérent avec l'existant)
- **Chargement** : client ChromaDB initialisé dans le lifespan FastAPI (comme le pool DB)

#### Nouveau fichier `core/rag.py`
```python
def index_example(pharmacy_id, question, sql)  → None
def retrieve_examples(pharmacy_id, question, n=3) → list[dict]
  # Retourne [{"question": ..., "sql": ...}, ...]
```

#### Modifications existantes
- `core/llm.py` : `build_sql_prompt(schema, question, examples=[])` — exemples optionnels
- `core/prompts/v1_sql_generation.txt` : ajouter bloc `<examples>` conditionnel
- `api/v1/chat/service.py` : appel RAG avant génération SQL
- `api/v1/feedback/service.py` : index ChromaDB si `rating == "good"`

#### Comportement si ChromaDB indisponible
RAG est best-effort : si `retrieve_examples` échoue, on génère le SQL sans exemples.
Ne jamais bloquer la réponse pour cause de RAG.

---

### Track 3 — JWT / RBAC

**Priorité : P2 — À faire en troisième**

Remplace les API keys statiques par des tokens JWT avec rôles.

#### Rôles
| Rôle | Accès |
|---|---|
| `pharmacist` | Lecture + feedback sur sa pharmacie (RLS inchangé) |
| `admin` | Accès `/admin/reload-manifest` + toutes les pharmacies |

#### Nouveaux endpoints
```
POST /api/v1/auth/login    { email, password } → { access_token, token_type, expires_in }
POST /api/v1/auth/refresh  { token } → { access_token, ... }
GET  /api/v1/auth/me       → { email, pharmacy_id, role }
```

#### Nouvelle table `raw.users`
```sql
CREATE TABLE raw.users (
  user_id       SERIAL PRIMARY KEY,
  email         VARCHAR(255) UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  pharmacy_id   INTEGER REFERENCES raw.pharmacies(pharmacy_id),
  role          VARCHAR(20) NOT NULL DEFAULT 'pharmacist'
                CHECK (role IN ('pharmacist', 'admin')),
  created_at    TIMESTAMP DEFAULT NOW()
);
```

#### Nouveaux fichiers
- `core/security.py` : `hash_password`, `verify_password`, `create_token`, `decode_token`
- `api/v1/auth/` : router + schemas + service

#### Modifications existantes
- `core/auth.py` : `get_current_pharmacy()` lit `Authorization: Bearer <jwt>` au lieu de `X-API-Key`
- `config.py` : `JWT_SECRET_KEY`, `JWT_ALGORITHM = "HS256"`, `JWT_EXPIRE_MINUTES = 1440`
- `requirements.txt` : ajouter `python-jose[cryptography]`, `passlib[bcrypt]`
- Frontend `api.js` : header `Authorization: Bearer` au lieu de `X-API-Key`
- Frontend : page Login avec formulaire email/mot de passe

#### Compatibilité ascendante
Pendant la transition, les API keys existantes restent valides en développement (`APP_ENV=development`). En production (`APP_ENV=production`), JWT uniquement.

---

## Modifications Infrastructure

### `requirements.txt` — 3 ajouts
```
chromadb>=0.6.0,<1.0.0
python-jose[cryptography]>=3.3.0,<4.0.0
passlib[bcrypt]>=1.7.4,<2.0.0
```

### `docker-compose.yml` — 1 ajout
```yaml
genbi_backend:
  volumes:
    - ./genbi_backend:/app
    - ./data/chromadb:/data/chromadb   # ← nouveau
```

### `data/postgres-init/init.sql` — 1 ajout
```sql
-- Table users pour JWT
CREATE TABLE IF NOT EXISTS raw.users (...);
```

---

## Stratégie de Test

| Couche | Quoi tester | Outil |
|---|---|---|
| `core/rag.py` | index + retrieve + isolation pharmacy | pytest unit |
| `core/security.py` | hash/verify password, encode/decode JWT | pytest unit |
| `api/v1/auth/` | login OK, mauvais mdp, token expiré | pytest integration |
| Endpoints protégés | JWT valide requis, rôle respecté | pytest integration |
| RAG flow | feedback good → indexé → retrouvé à la prochaine question | pytest integration |
| Frontend `useChat` | historique messages[], feedback state | Vitest |
| Frontend `FeedbackButtons` | vote unique, confirmation visuelle | Vitest |
| E2E conversation | historique visible, vote 👍 déclenchant indexation | Playwright |

---

## Critères de Succès

| ID | Critère | Mesure |
|---|---|---|
| CS-501 | Historique conversation visible en session | Vitest + Playwright |
| CS-502 | Bouton feedback déclenche `POST /feedback` | Playwright mock |
| CS-503 | Feedback `good` → exemple indexé dans ChromaDB | Test intégration |
| CS-504 | Question similaire → exemples injectés dans le prompt | Test unitaire |
| CS-505 | Login JWT → token valide → endpoints accessibles | Test intégration |
| CS-506 | Mauvais mot de passe → 401 | Test intégration |
| CS-507 | RAG indisponible → réponse quand même générée | Test unitaire mock |
| CS-508 | Isolation pharmacy : exemples RAG d'une pharmacie inaccessibles depuis une autre | Test intégration |

---

## Ordre d'Exécution

```
Track 1 (UX)   ─── semaine 1 ───►
Track 2 (RAG)          ─── semaines 1-2 ──────────────►
Track 3 (JWT)                    ─── semaines 2-3 ─────────────────────►
```

Track 1 en premier car 100% frontend, sans risque sur le backend.
Track 3 en dernier car il modifie l'authentification de tous les endpoints.

---

## Fichiers Clés à Créer / Modifier

```
À créer
  genbi_backend/core/rag.py
  genbi_backend/core/security.py
  genbi_backend/api/v1/auth/__init__.py
  genbi_backend/api/v1/auth/router.py
  genbi_backend/api/v1/auth/schemas.py
  genbi_backend/api/v1/auth/service.py
  genbi_backend/tests/unit/test_rag.py
  genbi_backend/tests/unit/test_security.py
  genbi_backend/tests/integration/test_auth_jwt.py
  genbi_frontend/src/components/chat/FeedbackButtons.jsx
  genbi_frontend/src/pages/LoginPage.jsx
  genbi_frontend/tests/unit/FeedbackButtons.test.jsx
  genbi_frontend/tests/unit/useChat_history.test.js

À modifier
  genbi_backend/core/llm.py              (exemples RAG dans build_sql_prompt)
  genbi_backend/core/prompts/v1_sql_generation.txt  (bloc <examples>)
  genbi_backend/core/auth.py             (JWT au lieu d'API key)
  genbi_backend/core/column_classifier.py (ajouter type "score" pour Phase 6)
  genbi_backend/api/v1/chat/service.py   (appel RAG)
  genbi_backend/api/v1/feedback/service.py (index ChromaDB)
  genbi_backend/main.py                  (lifespan ChromaDB + router auth)
  genbi_backend/requirements.txt         (3 nouvelles dépendances)
  genbi_backend/config.py                (JWT_SECRET_KEY, JWT_ALGORITHM, etc.)
  docker-compose.yml                     (volume chromadb)
  data/postgres-init/init.sql            (table users)
  genbi_frontend/src/hooks/useChat.js    (messages[] state)
  genbi_frontend/src/components/chat/ChatWindow.jsx  (render messages[])
  genbi_frontend/src/services/api.js     (Bearer token)
  genbi_frontend/src/App.jsx             (routing login/chat)
```
