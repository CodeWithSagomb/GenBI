#!/usr/bin/env python3
"""
Phase 5 — Génération corpus RAG synthétique via Claude Haiku.

Usage:
    docker exec genbi_backend python scripts/generate_rag_corpus.py

Ce script :
1. Interroge le schéma dbt compact depuis l'API
2. Envoie 6 lots thématiques à Claude Haiku (20 exemples chacun)
3. Valide chaque SQL contre la DB (pharmacy_id=1 = Bourguiba)
4. Indexe les exemples valides dans ChromaDB (partagé entre les 3 pharmacies)

Coût estimé : ~$0.10 avec claude-haiku-4-5
"""

import json
import sys

sys.path.insert(0, "/app")

import anthropic
import chromadb
import psycopg2

from config import settings
from core.rag import index_example

# ── Config ────────────────────────────────────────────────────────────────────

PHARMACY_ID = 1  # Bourguiba — pour valider les SQL (RLS actif)
MODEL = "claude-haiku-4-5-20251001"
EXAMPLES_PER_BATCH = 20

BATCHES = [
    {
        "theme": "CA et ventes",
        "instructions": (
            "Génère des questions sur le chiffre d'affaires et les ventes. "
            "Varie : CA total, CA par mois, CA par produit, CA par catégorie, "
            "CA par mode de paiement, CA par client, comparaisons temporelles."
        ),
    },
    {
        "theme": "Stocks et péremptions",
        "instructions": (
            "Génère des questions sur les stocks et les péremptions. "
            "Varie : produits sous seuil de sécurité, lots expirant dans X jours, "
            "stock par produit, stock par catégorie thérapeutique, lots déjà expirés."
        ),
    },
    {
        "theme": "Ruptures de stock",
        "instructions": (
            "Génère des questions sur les ruptures de stock (fct_missed_sales). "
            "Varie : nombre total de ruptures, ruptures par produit, ruptures par mois, "
            "produits avec le plus de ruptures, évolution des ruptures."
        ),
    },
    {
        "theme": "Clients et assureurs",
        "instructions": (
            "Génère des questions sur les clients et les assureurs. "
            "Varie : nombre de clients chroniques, clients assurés, "
            "répartition par assureur, panier moyen, meilleurs clients par points de fidélité."
        ),
    },
    {
        "theme": "Achats et retours fournisseurs",
        "instructions": (
            "Génère des questions sur les achats et retours fournisseurs. "
            "Varie : achats par mois, achats par grossiste, montant total des achats, "
            "retours fournisseurs, délais de livraison."
        ),
    },
    {
        "theme": "Analyses avancées",
        "instructions": (
            "Génère des questions complexes nécessitant des JOINs multi-tables. "
            "Varie : top produits par quantité ET par CA, génériques vs princeps, "
            "part tiers-payant, produits locaux vs importés, ventes par forme galénique, "
            "marge brute, activité par jour de semaine."
        ),
    },
]

# ── Prompt Haiku ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Tu es un expert SQL PostgreSQL pour pharmacies africaines.
Tu génères des paires Question→SQL strictement valides pour une pharmacie à Dakar.

RÈGLES CRITIQUES :
- Préfixes obligatoires : marts.fct_sales, marts.dim_products, staging.stg_raw__sale_details
- Alias standards : fct_sales=s · dim_products=pd · dim_stocks=sk · fct_purchases=fp · dim_clients=c · dim_insurers=ins
- NE PAS ajouter WHERE pharmacy_id (RLS automatique)
- Utiliser UNIQUEMENT les colonnes du schéma fourni
- Toujours GROUP BY quand SELECT contient une agrégation et une colonne non-agrégée
- dim_products JOIN ventes : passer par staging.stg_raw__sale_details sd
- COUNT DISTINCT produits : via sd.product_id (pas fct_sales)
- Différence de dates en jours : (date_col - CURRENT_DATE) sans INTERVAL
- dim_products alias TOUJOURS pd — jamais dp

RÈGLES ABSOLUES (violations = exemple rejeté) :
- ÉVOLUTION/TENDANCE : exactement 2 colonnes — (période, métrique). JAMAIS COUNT(*) ET SUM() dans le même SELECT d'évolution.
  ✓ SELECT sale_month AS mois, SUM(total_amount_fcfa) AS total_revenue FROM marts.fct_sales GROUP BY sale_month ORDER BY sale_month
  ✗ SELECT sale_month, COUNT(*) AS nb_ventes, SUM(total_amount_fcfa) AS ca FROM marts.fct_sales GROUP BY sale_month
- GÉNÉRIQUES : toujours CASE WHEN pour les labels — JAMAIS SELECT is_generic directement (retourne True/False illisible).
  ✓ SELECT CASE WHEN pd.is_generic THEN 'Générique' ELSE 'Princeps' END AS type_produit, SUM(...) ...
  ✗ SELECT pd.is_generic, SUM(...) FROM ... GROUP BY pd.is_generic
- MARGE : formule = SUM((pd.public_price_fcfa - fp.purchase_price_fcfa) * fp.quantity_ordered). quantity_ordered OBLIGATOIRE.
  ✗ SUM(pd.public_price_fcfa - fp.purchase_price_fcfa) — sans * fp.quantity_ordered donne résultat 100× trop faible
- RUPTURES : utiliser marts.fct_missed_sales — JAMAIS quantity_in_stock <= 0 ni quantity <= 0 (ces valeurs n'atteignent pas 0 dans les données)
- COUNT alias : COUNT(*) doit utiliser nb_* ou count_* — JAMAIS total_sales, total_orders (réservés aux montants FCFA)

SCHÉMA :
{schema}

Retourne UNIQUEMENT un tableau JSON valide, sans texte avant ni après :
[{{"question": "...", "sql": "SELECT ..."}}, ...]"""

USER_PROMPT = """Génère exactement {n} paires Question→SQL sur le thème : {theme}.

{instructions}

Les questions doivent être en français naturel (comme un pharmacien parlerait).
Le SQL doit être un SELECT valide sans point-virgule final.
Retourne UNIQUEMENT le tableau JSON."""


def get_schema() -> str:
    """Récupère le schéma compact depuis la DB."""
    conn = psycopg2.connect(
        host="postgres",
        port=5432,
        dbname=settings.DB_NAME,
        user=settings.DB_READONLY_USER,
        password=settings.DB_READONLY_PASSWORD,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_schema || '.' || table_name as tbl,
                       string_agg(column_name, ', ' ORDER BY ordinal_position) as cols
                FROM information_schema.columns
                WHERE table_schema IN ('marts', 'staging')
                  AND table_name IN (
                    'fct_sales', 'fct_purchases', 'fct_missed_sales',
                    'fct_wholesaler_returns', 'dim_products', 'dim_stocks',
                    'dim_clients', 'dim_insurers', 'dim_pharmacies',
                    'stg_raw__sale_details'
                  )
                GROUP BY table_schema, table_name
                ORDER BY table_schema, table_name
            """)
            rows = cur.fetchall()
        return "\n".join(f"{tbl}: {cols}" for tbl, cols in rows)
    finally:
        conn.close()


def is_semantically_valid(question: str, sql: str) -> bool:
    """Rejette les SQL qui passent l'exécution mais violent les règles métier.

    Ces patterns causent des régressions dans le RAG même si le SQL est syntaxiquement valide.
    """
    sql_l = sql.lower()
    q_l = question.lower()

    # Évolution 3 colonnes : COUNT + SUM ensemble sur une question temporelle
    evolution_kw = ("évol", "tendance", "par mois", "monthly", "trend", "mois")
    if any(k in q_l for k in evolution_kw):
        if "count(" in sql_l and "sum(" in sql_l:
            print(f"    ✗ REJETÉ (évolution 3 cols) : {question[:60]}")
            return False

    # is_generic direct → retourne True/False illisible
    if "is_generic" in sql_l and "case when" not in sql_l:
        print(f"    ✗ REJETÉ (is_generic sans CASE WHEN) : {question[:60]}")
        return False

    # Marge sans quantity_ordered
    if "purchase_price_fcfa" in sql_l and "public_price_fcfa" in sql_l:
        if "quantity_ordered" not in sql_l:
            print(f"    ✗ REJETÉ (marge sans quantity_ordered) : {question[:60]}")
            return False

    # Ruptures via quantity <= 0 (les données n'atteignent jamais 0)
    if ("quantity" in sql_l and "<= 0" in sql) or ("quantity_in_stock = 0" in sql_l):
        print(f"    ✗ REJETÉ (ruptures via quantity=0) : {question[:60]}")
        return False

    return True


def validate_sql(sql: str) -> bool:
    """Exécute le SQL avec RLS pharmacy_id=1 — retourne True si aucune erreur."""
    conn = psycopg2.connect(
        host="postgres",
        port=5432,
        dbname=settings.DB_NAME,
        user=settings.DB_READONLY_USER,
        password=settings.DB_READONLY_PASSWORD,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("SET app.current_pharmacy_id = %s", (PHARMACY_ID,))
            cur.execute(sql)
        return True
    except Exception as e:
        print(f"    ✗ SQL invalide : {e!s:.80}")
        return False
    finally:
        conn.close()


def generate_batch(client: anthropic.Anthropic, schema: str, batch: dict) -> list[dict]:
    """Appelle Claude Haiku pour un lot thématique."""
    print(f"\n→ Lot : {batch['theme']}")
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT.format(schema=schema),
        messages=[{
            "role": "user",
            "content": USER_PROMPT.format(
                n=EXAMPLES_PER_BATCH,
                theme=batch["theme"],
                instructions=batch["instructions"],
            ),
        }],
    )
    raw = response.content[0].text.strip()
    # Extraire le JSON même si Haiku ajoute du texte autour
    start = raw.find("[")
    end = raw.rfind("]") + 1
    if start == -1 or end == 0:
        print("  ⚠ Pas de JSON trouvé dans la réponse")
        return []
    return json.loads(raw[start:end])


def main():
    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        print("❌ ANTHROPIC_API_KEY vide dans .env — colle ta clé et relance.")
        sys.exit(1)

    print("Phase 5 — Génération corpus RAG synthétique")
    print(f"Modèle : {MODEL} · {len(BATCHES)} lots × {EXAMPLES_PER_BATCH} exemples")

    schema = get_schema()
    print(f"Schéma chargé : {len(schema)} caractères")

    haiku = anthropic.Anthropic(api_key=api_key)
    chroma = chromadb.PersistentClient(path=settings.CHROMADB_PATH)

    total_generated = 0
    total_valid = 0
    total_indexed = 0

    for batch in BATCHES:
        try:
            examples = generate_batch(haiku, schema, batch)
        except Exception as e:
            print(f"  ⚠ Erreur Haiku : {e}")
            continue

        print(f"  Générés : {len(examples)}")
        total_generated += len(examples)

        for ex in examples:
            q = ex.get("question", "").strip()
            sql = ex.get("sql", "").strip().rstrip(";")
            if not q or not sql or not sql.upper().startswith("SELECT"):
                continue

            if is_semantically_valid(q, sql) and validate_sql(sql):
                total_valid += 1
                for pharmacy_id in [1, 2, 3]:
                    index_example(chroma, pharmacy_id, q, sql)
                total_indexed += 1
                print(f"    ✓ [{total_indexed}] {q[:60]}")

    print(f"\n{'='*60}")
    print(f"Générés   : {total_generated}")
    print(f"Valides   : {total_valid}")
    print(f"Indexés   : {total_indexed} (× 3 pharmacies = {total_indexed * 3} entrées ChromaDB)")
    print("Phase 5 terminée.")


if __name__ == "__main__":
    main()
