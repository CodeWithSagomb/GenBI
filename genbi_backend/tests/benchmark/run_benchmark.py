"""
Benchmark qualité LLM — Phase 6 Track 1.

Usage (dans le container) :
    python3 tests/benchmark/run_benchmark.py
    python3 tests/benchmark/run_benchmark.py --verbose
    python3 tests/benchmark/run_benchmark.py --category ruptures

Critères de succès :
    PASS_SCALAR  : 1 ligne / 1 colonne — valeur dans la tolérance (2 %)
    PASS_COUNT   : N lignes retournées = N lignes golden
    FAIL_ERROR   : SQL génère une erreur PostgreSQL
    FAIL_EMPTY   : 0 lignes alors que golden en a
    FAIL_COUNT   : Nb de lignes incorrect
    FAIL_SCALAR  : Valeur scalaire hors tolérance
    FAIL_NO_SQL  : Le LLM n'a pas retourné de SQL
    SKIP_GOLDEN  : La golden_sql elle-même échoue (bug dans le benchmark)
"""

import sys
import json
import time
import urllib.request
import urllib.error
import argparse
from tests.benchmark.golden_questions import GOLDEN_QUESTIONS

BASE_URL = "http://localhost:8000"
DEFAULT_TOLERANCE = 0.02  # 2 %


# ── HTTP helper ───────────────────────────────────────────────────────────────

def _post(url: str, payload: dict, token: str | None = None) -> dict:
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode()[:200]}"}
    except Exception as e:
        return {"error": str(e)}


# ── Auth ──────────────────────────────────────────────────────────────────────

def get_token() -> str:
    resp = _post(
        f"{BASE_URL}/api/v1/auth/login",
        {"email": "bourguiba@pharma.sn", "password": "test123"},
    )
    if "access_token" not in resp:
        print("ERREUR : impossible de se connecter.", resp)
        sys.exit(1)
    return resp["access_token"]


# ── Comparaison ───────────────────────────────────────────────────────────────

def _scalar(result: dict) -> float | None:
    rows = result.get("rows", [])
    if len(rows) == 1 and len(rows[0]) == 1:
        try:
            return float(str(rows[0][0]).replace(",", "."))
        except (TypeError, ValueError):
            return None
    return None


def compare(q: dict, generated: dict, golden: dict) -> dict:
    if "error" in generated:
        return {"status": "FAIL_ERROR", "detail": generated["error"][:120]}

    gen_rows = generated.get("rows", [])
    gold_rows = golden.get("rows", [])

    if len(gen_rows) == 0 and len(gold_rows) > 0:
        return {"status": "FAIL_EMPTY", "detail": f"0 lignes (golden: {len(gold_rows)})"}

    # Cas scalaire
    tol = q.get("tolerance", DEFAULT_TOLERANCE)
    gen_scalar = _scalar(generated)
    gold_scalar = _scalar(golden)

    if gold_scalar is not None and gen_scalar is not None:
        ref = gold_scalar if gold_scalar != 0 else 1
        diff = abs(gen_scalar - gold_scalar) / abs(ref)
        if diff <= tol:
            return {"status": "PASS_SCALAR", "detail": f"LLM:{gen_scalar:.0f} | Golden:{gold_scalar:.0f}"}
        return {"status": "FAIL_SCALAR", "detail": f"LLM:{gen_scalar:.0f} | Golden:{gold_scalar:.0f} (diff:{diff:.1%})"}

    # Cas multi-lignes : comparer le nombre de lignes
    expected_rows = q.get("expected_rows")
    if expected_rows is not None:
        if len(gen_rows) == expected_rows:
            return {"status": "PASS_COUNT", "detail": f"rows:{len(gen_rows)}/{expected_rows}"}
        return {"status": "FAIL_COUNT", "detail": f"rows:{len(gen_rows)} attendu:{expected_rows}"}

    # Pas de contrainte définie — on vérifie juste que le SQL tourne
    if len(gen_rows) > 0:
        return {"status": "PASS_COUNT", "detail": f"rows:{len(gen_rows)} (non contraint)"}
    return {"status": "FAIL_EMPTY", "detail": "0 lignes retournées"}


# ── Runner ────────────────────────────────────────────────────────────────────

def run_question(q: dict, token: str, verbose: bool = False) -> dict:
    t0 = time.time()

    # Valider d'abord le golden SQL
    golden_result = _post(
        f"{BASE_URL}/api/v1/execute", {"sql": q["golden_sql"]}, token
    )
    if "error" in golden_result:
        return {
            **q,
            "status": "SKIP_GOLDEN",
            "detail": f"golden_sql invalide: {golden_result['error'][:100]}",
            "elapsed": round(time.time() - t0, 1),
        }

    # Appeler le LLM
    chat_result = _post(
        f"{BASE_URL}/api/v1/chat", {"question": q["question"]}, token
    )
    generated_sql = chat_result.get("sql", "")

    if not generated_sql:
        return {
            **q,
            "status": "FAIL_NO_SQL",
            "detail": str(chat_result)[:100],
            "elapsed": round(time.time() - t0, 1),
        }

    if verbose:
        print(f"  SQL LLM : {generated_sql.replace(chr(10), ' ')[:120]}")

    # Exécuter le SQL généré
    generated_result = _post(
        f"{BASE_URL}/api/v1/execute", {"sql": generated_sql}, token
    )

    verdict = compare(q, generated_result, golden_result)
    return {
        **q,
        **verdict,
        "generated_sql": generated_sql,
        "elapsed": round(time.time() - t0, 1),
    }


# ── Rapport ───────────────────────────────────────────────────────────────────

ICONS = {
    "PASS_SCALAR": "✅",
    "PASS_COUNT":  "✅",
    "FAIL_ERROR":  "❌",
    "FAIL_EMPTY":  "❌",
    "FAIL_COUNT":  "⚠️ ",
    "FAIL_SCALAR": "⚠️ ",
    "FAIL_NO_SQL": "❌",
    "SKIP_GOLDEN": "⏭️ ",
}

def print_report(results: list[dict]) -> None:
    passed = [r for r in results if r["status"].startswith("PASS")]
    failed = [r for r in results if r["status"].startswith("FAIL")]
    skipped = [r for r in results if r["status"].startswith("SKIP")]
    total = len(results) - len(skipped)

    print("\n" + "═" * 72)
    print("BENCHMARK QUALITÉ LLM — GenBI Phase 6")
    print("═" * 72)

    for r in results:
        icon = ICONS.get(r["status"], "❓")
        line = f"{icon} {r['id']} [{r['category']:10s}] {r['question'][:48]:<48}"
        line += f"  {r['status']:<14} {r.get('detail','')[:35]}"
        line += f"  ({r.get('elapsed', 0):.1f}s)"
        print(line)

    print("─" * 72)

    # Par catégorie
    cats = {}
    for r in results:
        if r["status"].startswith("SKIP"):
            continue
        c = r["category"]
        cats.setdefault(c, {"pass": 0, "total": 0})
        cats[c]["total"] += 1
        if r["status"].startswith("PASS"):
            cats[c]["pass"] += 1

    print("\nPar catégorie :")
    for cat, v in cats.items():
        bar = "█" * v["pass"] + "░" * (v["total"] - v["pass"])
        print(f"  {cat:12s} {v['pass']}/{v['total']}  {bar}")

    score_pct = int(len(passed) / total * 100) if total > 0 else 0
    print(f"\n{'═' * 72}")
    print(f"SCORE FINAL : {len(passed)}/{total}  ({score_pct} %)")
    if skipped:
        print(f"Skipped (golden_sql invalide) : {len(skipped)}")
    if failed:
        print(f"\nÉchecs à corriger ({len(failed)}) :")
        for r in failed:
            print(f"  {r['id']} {r['question'][:55]}")
            print(f"       → {r.get('detail','')}")
    print("═" * 72 + "\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark qualité LLM GenBI")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--category", "-c", default=None,
                        help="Filtrer par catégorie (ca_simple, produits, clients, ruptures, stats, complexe)")
    parser.add_argument("--id", default=None, help="Tester une seule question (ex: Q01)")
    args = parser.parse_args()

    questions = GOLDEN_QUESTIONS
    if args.category:
        questions = [q for q in questions if q["category"] == args.category]
    if args.id:
        questions = [q for q in questions if q["id"] == args.id]

    if not questions:
        print("Aucune question ne correspond aux filtres.")
        sys.exit(1)

    print(f"Connexion à {BASE_URL}...")
    token = get_token()
    print(f"Authentifié ✓  —  {len(questions)} question(s) à tester\n")

    results = []
    for i, q in enumerate(questions, 1):
        print(f"[{i:02d}/{len(questions):02d}] {q['id']} — {str(q['question'])[:55]}", end="", flush=True)
        r = run_question(q, token, verbose=args.verbose)
        icon = ICONS.get(r["status"], "❓")
        print(f"  {icon} {r['status']}  ({r.get('elapsed', 0):.1f}s)")
        results.append(r)

    print_report(results)


if __name__ == "__main__":
    main()
