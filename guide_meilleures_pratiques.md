# Guide des Meilleures Pratiques — Projet GenBI

Ce document synthétise les standards de l'ingénierie logicielle moderne appliqués à chaque couche du projet GenBI. Il sert de référence pour chaque décision technique prise au cours du développement.

---

## 1. Philosophie Générale : Start Simple, Add Complexity Deliberately

> *"Find the simplest solution possible, and only increasing complexity when needed."* — Anthropic

Le principe fondateur qui guide toute la construction :
- Chaque composant doit avoir une responsabilité unique et claire.
- Ajouter de la complexité (agents multi-steps, RAG, orchestration) **seulement quand la version simple atteint ses limites**.
- Préférer des **workflows déterministes** (chaîne de prompts prédéfinie) aux agents autonomes tant que le domaine est bien défini.

---

## 2. Couche LLM — Intégration Claude / Ollama (Backend)

### 2.1 Architecture du Prompt Text-to-SQL

La différence entre 40% et 95% de précision n'est pas le modèle — c'est la qualité du contexte injecté.

**Structure du prompt (ordre obligatoire) :**
```
[1] System Prompt  : Rôle, règles de sécurité, instructions SQL (PostgreSQL dialect)
[2] Contexte dbt   : Métadonnées des tables/colonnes extraites du manifest.json (AVANT la question)
[3] Exemples RAG   : 3-5 exemples question→SQL similaires récupérés dans ChromaDB
[4] Question user  : La question en langage naturel (TOUJOURS en dernier)
```

Mettre le contexte AVANT la question améliore la précision jusqu'à 30% (source Anthropic).

**Utiliser les balises XML pour structurer les sections du prompt :**
```xml
<dbt_schema>
  Table: marts.fct_sales — Table des faits de ventes
  Colonnes: sale_id, sale_date, total_amount_fcfa, client_type, pharmacy_id...
  Relations: FK vers dim_clients, dim_products, dim_pharmacies
</dbt_schema>

<few_shot_examples>
  Q: "Quel est le CA total du mois de Mars ?"
  SQL: SELECT SUM(total_amount_fcfa) FROM marts.fct_sales WHERE DATE_TRUNC('month', sale_date) = '2026-03-01'
</few_shot_examples>

<user_question>
  {question}
</user_question>
```

### 2.2 Sécurité de l'Exécution SQL (Guardrails)

**Importante nuance sur SQLGlot** : SQLGlot est un *parseur/transpileur*, **pas un validateur de sécurité**. Il ne détecte pas les injections SQL par conception. La sécurité repose sur :

1. **Couche 1 (Architecture)** : L'agent IA se connecte UNIQUEMENT avec l'user `genbi_readonly` (SELECT only, jamais DROP/DELETE/INSERT). C'est la défense la plus robuste.
2. **Couche 2 (Parsing)** : SQLGlot parse la requête pour détecter les instructions non-SELECT (DDL, DML) — rejeter toute requête contenant `INSERT`, `UPDATE`, `DELETE`, `DROP`, `TRUNCATE`, `CREATE`.
3. **Couche 3 (Paramétrage)** : Utiliser des requêtes paramétrées via psycopg2 — ne jamais interpoler de strings directement dans le SQL.

```python
# INTERDIT — injection possible
cursor.execute(f"SELECT * FROM marts.fct_sales WHERE pharmacy_id = {user_input}")

# CORRECT — paramétré
cursor.execute("SELECT * FROM marts.fct_sales WHERE pharmacy_id = %s", (pharmacy_id,))
```

### 2.3 Effort et Modèle LLM

Pour le modèle Ollama local (`qwen2.5-coder:7b`), configurer via le paramètre température :
- `temperature=0.0` pour la génération SQL (déterminisme total).
- `temperature=0.3` pour les réponses en langage naturel.

Si l'on migre vers Claude API (cloud) :
- Utiliser `claude-sonnet-4-6` pour le text-to-SQL (rapport qualité/coût optimal).
- Effort `xhigh` pour les tâches de code/SQL, `high` pour les réponses analytiques.

---

## 3. Couche dbt — Modélisation des Données (Phase 2)

### 3.1 Conventions de Nommage Obligatoires

| Couche | Préfixe | Exemple | Matérialisation |
|---|---|---|---|
| Sources | (aucun) | `raw.sales` | Table (source) |
| Staging | `stg_[source]__[entité]s` | `stg_raw__sales` | **View** |
| Intermédiaire | `int_[entité]s__[verbe]` | `int_sales__aggregated` | View ou Ephemeral |
| Marts - Faits | `fct_[entité]s` | `fct_sales` | **Table** |
| Marts - Dimensions | `dim_[entité]s` | `dim_products` | **Table** |

Le **double underscore** (`__`) sépare la source de l'entité dans les noms de staging.

### 3.2 Structure des Dossiers

```
dbt_project/
├── models/
│   ├── staging/
│   │   └── raw/
│   │       ├── _raw__sources.yml        # Déclaration des sources raw
│   │       ├── _raw__models.yml         # Documentation + tests staging
│   │       ├── stg_raw__pharmacies.sql
│   │       ├── stg_raw__products.sql
│   │       ├── stg_raw__clients.sql
│   │       ├── stg_raw__insurers.sql
│   │       ├── stg_raw__sales.sql
│   │       ├── stg_raw__sale_details.sql
│   │       ├── stg_raw__stocks.sql
│   │       ├── stg_raw__purchases.sql
│   │       ├── stg_raw__missed_sales.sql
│   │       └── stg_raw__wholesaler_returns.sql
│   └── marts/
│       ├── pharmacy/
│       │   ├── _pharmacy__models.yml    # Documentation + tests marts
│       │   ├── fct_sales.sql            # Table de faits principale
│       │   ├── fct_purchases.sql
│       │   ├── fct_missed_sales.sql
│       │   ├── dim_products.sql
│       │   ├── dim_clients.sql
│       │   ├── dim_pharmacies.sql
│       │   └── dim_insurers.sql
│       └── finance/
│           └── fct_insurer_receivables.sql  # Créances Tiers-Payant
├── tests/
├── macros/
├── dbt_project.yml
└── profiles.yml
```

### 3.3 Règles Strictes par Couche

**Staging — Autorisé :**
- Renommage de colonnes (`id` → `product_id`)
- Cast de types (`amount::int`, `sale_date::timestamp`)
- Calculs simples (`amount / 100.0 as amount_xof`)
- `CASE WHEN` pour catégoriser

**Staging — Interdit :**
- Jointures entre tables (jamais dans staging)
- Agrégations (`GROUP BY`, `SUM`, `COUNT`)
- Logique métier complexe

**Marts — Principes :**
- Tables larges et dénormalisées (le stockage est bon marché, la compute non)
- Toutes les jointures et la logique métier ici
- Chaque colonne doit avoir une `description:` dans le YAML (utilisée par l'IA)

### 3.4 Documentation YAML — Standard Obligatoire

La description de chaque colonne dans le manifest.json est le **contexte que l'IA consomme**. C'est critique.

```yaml
# models/marts/pharmacy/_pharmacy__models.yml
version: 2

models:
  - name: fct_sales
    description: >
      Table de faits des ventes d'officine. Grain : une ligne par vente (en-tête).
      Couvre les ventes au comptoir, le tiers-payant, et les paiements mobiles (Wave, Orange Money).
      Données du 1er Mars 2026 à aujourd'hui pour les 3 pharmacies de Dakar.
    columns:
      - name: sale_id
        description: "Identifiant unique de la vente."
        data_tests: [unique, not_null]
      - name: total_amount_fcfa
        description: "Montant total de la vente en Francs CFA XOF. Entier strict (pas de centimes)."
        data_tests: [not_null]
      - name: patient_share_fcfa
        description: "Part payée par le patient (ticket modérateur). Égal à total si paiement comptant."
      - name: insurer_share_fcfa
        description: "Part prise en charge par l'assureur/IPM (tiers-payant). 0 si paiement comptant."
      - name: payment_method
        description: "Mode de paiement : 'Espèces', 'Wave', 'Orange Money', 'Tiers-Payant'."
      - name: client_type
        description: "Type de client : 'Passant' (anonyme), 'Assuré' (mutuelle/IPM)."
```

### 3.5 Tests dbt Obligatoires

```yaml
# Tests minimaux sur chaque clé primaire et FK
data_tests:
  - unique
  - not_null
  - relationships:
      to: ref('dim_products')
      field: product_id
  - accepted_values:
      values: ['Espèces', 'Wave', 'Orange Money', 'Tiers-Payant']
```

---

## 4. Backend FastAPI — Architecture par Domaine (Phase 3)

### 4.1 Structure de Dossiers (Domain-Driven)

```
genbi_backend/
├── main.py                   # App factory + middleware + routers
├── config.py                 # Settings Pydantic (déjà en place)
├── dependencies.py           # DB connections partagées (DI)
├── api/
│   ├── v1/
│   │   ├── chat/
│   │   │   ├── router.py     # Endpoint POST /api/v1/chat
│   │   │   ├── schemas.py    # Pydantic models (ChatRequest, ChatResponse)
│   │   │   └── service.py    # Logique métier : prompt → LLM → SQL
│   │   ├── execute/
│   │   │   ├── router.py     # Endpoint POST /api/v1/execute
│   │   │   ├── schemas.py    # SQLRequest, QueryResult
│   │   │   └── service.py    # Validation SQLGlot + exécution psycopg2
│   │   └── schema/
│   │       ├── router.py     # Endpoint GET /api/v1/schema
│   │       └── service.py    # Parser manifest.json dbt
├── core/
│   ├── llm.py                # Client Ollama/LiteLLM
│   ├── dbt_parser.py         # Lecture et cache du manifest.json
│   ├── sql_validator.py      # Validation SQLGlot + whitelist SELECT
│   └── rag.py                # Client ChromaDB (Phase 5)
└── requirements.txt
```

### 4.2 Règles de Code FastAPI

**Async obligatoire pour les routes I/O-bound :**
```python
# CORRECT — async pour tout appel DB ou LLM
@router.post("/chat")
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    sql = await llm_service.generate_sql(request.question)
    return ChatResponse(sql=sql)
```

**Dependency Injection pour les connexions DB :**
```python
# dependencies.py
from psycopg2.pool import ThreadedConnectionPool

pool = ThreadedConnectionPool(1, 10, dsn=settings.readonly_dsn)

def get_readonly_db():
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)

# Usage dans un router
@router.post("/execute")
async def execute_sql(
    request: SQLRequest,
    db=Depends(get_readonly_db)
) -> QueryResult:
    ...
```

**CORS — Restreindre en production :**
```python
# main.py — Ne pas laisser allow_origins=["*"] en prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],  # Ex: "http://localhost:5173"
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
```

**Gestion des erreurs — Toujours retourner du JSON :**
```python
from fastapi import HTTPException

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(status_code=400, content={"error": str(exc)})
```

### 4.3 Service de Validation SQL (sql_validator.py)

```python
import sqlglot
from sqlglot import exp

FORBIDDEN_STATEMENT_TYPES = (
    exp.Insert, exp.Update, exp.Delete,
    exp.Drop, exp.Create, exp.Truncate, exp.AlterTable
)

def validate_sql(query: str) -> str:
    """Parse et valide que la requête est un SELECT pur. Lève ValueError sinon."""
    try:
        statements = sqlglot.parse(query, dialect="postgres")
    except sqlglot.errors.ParseError as e:
        raise ValueError(f"SQL invalide : {e}")

    if not statements:
        raise ValueError("Requête vide.")

    for stmt in statements:
        if isinstance(stmt, FORBIDDEN_STATEMENT_TYPES):
            raise ValueError(f"Opération interdite détectée : {type(stmt).__name__}")
        if not isinstance(stmt, exp.Select):
            raise ValueError("Seules les requêtes SELECT sont autorisées.")

    return query
```

### 4.4 Parser dbt manifest.json (dbt_parser.py)

```python
import json
from functools import lru_cache

@lru_cache(maxsize=1)
def load_dbt_schema(manifest_path: str) -> str:
    """Charge et formate les métadonnées dbt pour injection dans le prompt LLM."""
    with open(manifest_path) as f:
        manifest = json.load(f)

    schema_lines = []
    for node_key, node in manifest.get("nodes", {}).items():
        if node["resource_type"] != "model" or not node_key.startswith("model."):
            continue
        if node["config"]["schema"] not in ("staging", "marts"):
            continue

        table_name = f"{node['config']['schema']}.{node['name']}"
        description = node.get("description", "Pas de description.")
        schema_lines.append(f"\nTable: {table_name}")
        schema_lines.append(f"  Description: {description}")

        for col_name, col_info in node.get("columns", {}).items():
            col_desc = col_info.get("description", "")
            schema_lines.append(f"  - {col_name}: {col_desc}")

    return "\n".join(schema_lines)
```

---

## 5. Airflow DAGs — Pipeline de Données (Phase 1 — Amélioration Continue)

### 5.1 Idempotence Absolue

Chaque tâche doit produire le même résultat qu'elle soit exécutée 1 ou 10 fois.

- Toujours utiliser `CREATE TABLE IF NOT EXISTS` (déjà fait).
- Utiliser `TRUNCATE ... CASCADE` avant les inserts en bulk (déjà fait).
- Pour les ingestions futures (APIs externes), utiliser `INSERT ... ON CONFLICT (id) DO UPDATE`.

### 5.2 Atomicité des Tâches

Chaque tâche = une seule responsabilité. Le DAG actuel est correct avec ses 2 tâches :
```
create_pharmacy_schema >> populate_pharmacy_data
```

Si on ajoute de nouvelles sources, ajouter des tâches spécifiques, pas alourdir les fonctions existantes.

### 5.3 Connexion à PostgreSQL

Toujours passer par `PostgresHook` (déjà fait), jamais hardcoder les credentials dans le DAG. La connexion `genbi_postgres_conn` doit être configurée dans l'UI Airflow.

### 5.4 Logging

```python
logger = logging.getLogger("airflow.task")
logger.info(f"✓ {len(sales)} ventes insérées.")
logger.warning(f"⚠ Rupture détectée : produit {prod_id}")
```

---

## 6. Frontend React + Vite — Interface Chat (Phase 4)

### 6.1 Architecture Composants

```
genbi_frontend/src/
├── components/
│   ├── chat/
│   │   ├── ChatWindow.jsx       # Conteneur principal du chat
│   │   ├── MessageBubble.jsx    # Bulle de message (user / IA)
│   │   ├── SQLDisplay.jsx       # Affichage syntaxe SQL avec highlighting
│   │   └── QueryInput.jsx       # Barre de saisie + bouton Envoyer
│   ├── visualizations/
│   │   ├── DataTable.jsx        # Tableau de résultats
│   │   ├── BarChart.jsx         # Recharts BarChart
│   │   ├── LineChart.jsx        # Recharts LineChart
│   │   └── ChartRouter.jsx      # Sélectionne automatiquement le bon graphique
│   └── layout/
│       ├── Header.jsx
│       └── StatusBadge.jsx
├── hooks/
│   ├── useChat.js               # Logique de state du chat + appels API
│   └── useSchema.js             # Fetch du /schema au démarrage
├── services/
│   └── api.js                   # Client HTTP centralisé (fetch vers FastAPI)
├── App.jsx
├── main.jsx
└── index.css
```

### 6.2 Service API Centralisé

```javascript
// services/api.js
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const chatApi = {
  async sendQuestion(question) {
    const res = await fetch(`${API_BASE}/api/v1/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  },

  async executeSQL(sql) {
    const res = await fetch(`${API_BASE}/api/v1/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql })
    })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }
}
```

### 6.3 UX du Flux Chat (Étape par Étape)

Le flow affiché à l'utilisateur doit montrer chaque étape pour créer de la confiance :

```
[1] Question utilisateur : "Quel produit s'est le mieux vendu ce mois-ci ?"
[2] 🔄 Analyse en cours...
[3] SQL généré :
    SELECT p.commercial_name, SUM(sd.quantity) as total_sold
    FROM marts.fct_sales fs
    JOIN marts.dim_products p ON fs.product_id = p.product_id
    ...
[4] Tableau de résultats + Graphique Recharts
```

---

## 7. RAG & ChromaDB — Phase 5

### 7.1 Ce qu'on stocke dans ChromaDB

Uniquement des **exemples question→SQL validés** (corrigés par un humain ou confirmés corrects) :

```python
collection.add(
    documents=["Quel est le chiffre d'affaires total du mois de Mars 2026 ?"],
    metadatas=[{"sql": "SELECT SUM(total_amount_fcfa) FROM marts.fct_sales WHERE ..."}],
    ids=["example_001"]
)
```

### 7.2 Embedding et Retrieval

Au moment d'une question utilisateur :
1. Embed la question avec le même modèle d'embedding (ex: `nomic-embed-text` via Ollama).
2. Récupérer les 3-5 exemples les plus similaires depuis ChromaDB.
3. Les injecter dans le prompt comme `<few_shot_examples>`.

### 7.3 Feedback Loop Humain

Le frontend doit proposer deux boutons sous chaque résultat :
- ✅ **"SQL correct"** → enregistre l'exemple dans ChromaDB automatiquement.
- ✏️ **"Corriger le SQL"** → ouvre un éditeur SQL inline, l'utilisateur valide, et on enregistre la version corrigée.

---

## 8. Sécurité — Checklist Complète

| Point | Status | Action |
|---|---|---|
| User DB read-only pour l'IA | ✅ Fait | `genbi_readonly` en place dans init.sql |
| Pas de credentials en dur dans le code | ✅ Fait | Variables d'env via `.env` |
| `.env` dans `.gitignore` | ✅ Fait | Vérifié |
| CORS restreint | ⚠️ À faire | Changer `allow_origins=["*"]` en production |
| Validation SELECT-only avant exécution | ⏳ Phase 3 | Implémenter `sql_validator.py` |
| Paramétrage des requêtes psycopg2 | ⏳ Phase 3 | Ne jamais interpoler les paramètres |
| Rate limiting sur `/chat` | ⏳ Futur | `slowapi` ou middleware custom |
| Logging des requêtes générées | ⏳ Phase 3 | Audit trail de chaque SQL exécuté |

---

## 9. Ordre de Développement Recommandé

```
Phase 2 (BLOQUANT pour tout le reste)
  └── Initialiser dbt-core
  └── Créer les 10 modèles staging (stg_raw__*)
  └── Créer les marts (fct_sales, dim_products, dim_clients, dim_pharmacies, dim_insurers)
  └── Documenter toutes les colonnes dans les YAML
  └── Exécuter `dbt run` + `dbt test`
  └── Vérifier que target/manifest.json est généré

Phase 3 (Backend)
  └── Implémenter dbt_parser.py (lecture manifest.json)
  └── Implémenter le prompt text-to-SQL + client Ollama
  └── Implémenter sql_validator.py
  └── Endpoint /api/v1/schema (retourne les tables disponibles)
  └── Endpoint /api/v1/chat (question → SQL)
  └── Endpoint /api/v1/execute (SQL → résultats JSON)

Phase 4 (Frontend)
  └── Hook useSchema (charge les tables au démarrage)
  └── Hook useChat (gère le flow question→sql→résultats)
  └── Composants ChatWindow + MessageBubble
  └── SQLDisplay avec syntax highlighting
  └── ChartRouter + composants Recharts

Phase 5 (RAG)
  └── Initialiser ChromaDB avec premiers exemples
  └── Intégrer le retrieval dans le prompt builder
  └── Boutons feedback dans le frontend
```

---

*Sources : [Anthropic — Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) · [Claude Prompting Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) · [dbt Staging Best Practices](https://docs.getdbt.com/best-practices/how-we-structure/2-staging) · [dbt Marts](https://docs.getdbt.com/best-practices/how-we-structure/4-marts) · [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices) · [Astronomer — Airflow DAG Best Practices](https://www.astronomer.io/docs/learn/dag-best-practices/) · [Semantic Layer vs Text-to-SQL 2026](https://docs.getdbt.com/blog/semantic-layer-vs-text-to-sql-2026)*
