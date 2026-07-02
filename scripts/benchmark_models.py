"""
test_compare_14b.py — Benchmark comparatif qwen2.5-coder:7b vs 14b — RuwaGenBI
Usage :
    python3 test_compare_14b.py --model 7b   # baseline 7b
    python3 test_compare_14b.py --model 14b  # test 14b
    python3 test_compare_14b.py --quick      # 10 premières questions seulement
    python3 test_compare_14b.py --id T09     # tester une seule question
    python3 test_compare_14b.py --save       # sauvegarder résultats JSON dans /tmp/
"""

import json, time, sys, argparse, urllib.request, urllib.error
from dataclasses import dataclass, asdict
from typing import Optional

BASE_URL = "http://localhost:8000"

# ── 20 questions comparatives ──────────────────────────────────────────────────
# (id, question, category, difficulty, tour2_si_multitour)
QUESTIONS = [
    ("T01", "Quel est mon CA total ?",                                                        "simple",       "easy",      None),
    ("T02", "Donne-moi le top 5 produits par chiffre d affaires",                             "join",         "easy",      None),
    ("T03", "Combien de ventes tiers-payant ce mois-ci ?",                                    "temporal",     "medium",    None),
    ("T04", "Quelle est l evolution mensuelle de mon CA depuis le debut de l annee ?",        "group_by",     "medium",    None),
    ("T05", "Quelles sont mes 5 classes therapeutiques les plus vendues ?",                   "group_by",     "medium",    None),
    ("T06", "Quel est mon taux de service par grossiste en avril 2026 ?",                     "aggregation",  "hard",      None),
    ("T07", "Quel est le panier moyen par type de client ?",                                  "aggregation",  "medium",    None),
    ("T08", "Combien de medicaments generiques avons-nous vendus par mois ?",                 "join_filter",  "hard",      None),
    ("T09", "Quels sont les lots de medicaments qui expirent dans moins de 30 jours ?",      "stocks",       "hard",      None),
    ("T10", "Quel est le CA genere par les clients de l assureur IPRES ?",                    "join_triple",  "hard",      None),
    ("T11", "C est quoi les produits qu on vend le plus aux clients chroniques ?",            "ambiguous",    "hard",      None),
    ("T12", "Montre-moi l evolution des ruptures de stock mois par mois",                     "ruptures",     "medium",    None),
    ("T13", "Quel est le delai moyen de livraison de mes fournisseurs ?",                     "purchases",    "hard",      None),
    ("T14", "Quels produits importes se vendent le mieux ?",                                  "filter_domain","medium",    None),
    ("T15", "Donne-moi la marge brute estimee par produit",                                   "margin",       "very_hard", None),
    ("T16", "En fevrier, quels medicaments ont ete le plus retournes aux fournisseurs ?",     "returns",      "hard",      None),
    ("T17", "Quels sont mes 5 meilleurs produits ?",                                          "multiturn",    "very_hard", "Et parmi eux, lesquels sont des generiques ?"),
    ("T18", "Quel est le CA d avril 2026 ?",                                                  "multiturn",    "hard",      "Compare avec mars"),
    ("T19", "Quelle est la part des ventes Tiers-Payant par rapport au total ?",              "ambiguous",    "medium",    None),
    ("T20", "Quels medicaments n ont jamais ete vendus ce mois-ci ?",                         "anti_join",    "very_hard", None),
]

# ── HTTP helpers ───────────────────────────────────────────────────────────────

def _post(path, payload, token=None, timeout_s=130):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode()[:300]}"}
    except Exception as e:
        return {"error": str(e)}

def get_token():
    resp = _post("/api/v1/auth/login",
                 {"email": "bourguiba@pharma.sn", "password": "test123"}, timeout_s=10)
    if "access_token" not in resp:
        print(f"AUTH FAILED: {resp}"); sys.exit(1)
    return resp["access_token"]

# ── Résultat par question ──────────────────────────────────────────────────────

@dataclass
class QResult:
    id: str
    question: str
    category: str
    difficulty: str
    latency_ms: float = 0.0
    sql_success: bool = False
    sql_generated: str = ""
    rows_returned: int = 0
    error_detail: str = ""
    tour2_question: Optional[str] = None
    tour2_latency_ms: float = 0.0
    tour2_success: bool = False
    tour2_rows: int = 0

def run_question(qid, question, category, difficulty, tour2, token):
    r = QResult(id=qid, question=question, category=category,
                difficulty=difficulty, tour2_question=tour2)

    t0 = time.time()
    resp = _post("/api/v1/analyse", {"question": question}, token)
    r.latency_ms = round((time.time() - t0) * 1000, 1)

    sa = resp.get("sub_analyses", [{}])[0] if not resp.get("error") else {}
    sql = sa.get("sql", "")
    r.sql_generated = sql

    if not sql:
        r.error_detail = resp.get("error", "NO_SQL")[:150]
        return r

    exec_resp = _post("/api/v1/execute", {"sql": sql, "limit": 50}, token)
    if "error" in exec_resp:
        r.error_detail = exec_resp["error"][:200]
    else:
        r.sql_success = True
        r.rows_returned = len(exec_resp.get("rows", []))

    # Multi-tour
    if tour2 and r.sql_success:
        history = [
            {"role": "user",      "content": question},
            {"role": "assistant", "content": sql},
        ]
        t1 = time.time()
        resp2 = _post("/api/v1/analyse",
                      {"question": tour2, "conversation_history": history}, token)
        r.tour2_latency_ms = round((time.time() - t1) * 1000, 1)
        sa2 = resp2.get("sub_analyses", [{}])[0] if not resp2.get("error") else {}
        sql2 = sa2.get("sql", "")
        if sql2:
            exec2 = _post("/api/v1/execute", {"sql": sql2, "limit": 50}, token)
            r.tour2_success = "error" not in exec2
            r.tour2_rows = len(exec2.get("rows", []))

    return r

# ── Rapport ────────────────────────────────────────────────────────────────────

def print_report(results, model_name):
    print(f"\n{'═'*80}")
    print(f"  BENCHMARK — {model_name}")
    print(f"{'═'*80}")
    print(f"{'ID':<4} {'Catégorie':14} {'Diff':10} {'Latence':>9} {'OK':>3} {'Rows':>5}  Détail")
    print(f"{'─'*80}")

    success = 0
    latencies = []
    for r in results:
        ok = "✅" if r.sql_success else "❌"
        if r.sql_success:
            success += 1
            latencies.append(r.latency_ms)
        lat = f"{r.latency_ms/1000:.1f}s"
        detail = r.error_detail[:38] if not r.sql_success else r.sql_generated[:38].replace('\n',' ')
        print(f"{r.id:<4} {r.category:14} {r.difficulty:10} {lat:>9} {ok:>3} {r.rows_returned:>5}  {detail}")
        if r.tour2_question:
            ok2 = "✅" if r.tour2_success else "❌"
            print(f"  └─ Tour2: {ok2} {r.tour2_latency_ms/1000:.1f}s  rows={r.tour2_rows}")

    print(f"{'─'*80}")
    total = len(results)
    pct = round(100 * success / total) if total else 0
    lat_sorted = sorted(latencies)
    p50 = lat_sorted[len(lat_sorted)//2] if lat_sorted else 0
    p95 = lat_sorted[int(len(lat_sorted)*0.95)] if lat_sorted else 0

    print(f"\n  Score SQL   : {success}/{total} ({pct}%)")
    print(f"  Latence P50 : {p50/1000:.1f}s")
    print(f"  Latence P95 : {p95/1000:.1f}s")
    print()
    for diff in ["easy", "medium", "hard", "very_hard"]:
        sub = [r for r in results if r.difficulty == diff]
        s = sum(1 for r in sub if r.sql_success)
        if sub: print(f"  {diff:12}: {s}/{len(sub)}")

    # Verdict
    print(f"\n{'─'*80}")
    if pct >= 80 and p50 < 12000:
        print(f"  VERDICT ✅ : {model_name} performant — garder si P6 >= 96%")
    elif pct >= 80 and p50 >= 12000:
        print(f"  VERDICT ⚠️  : Score OK mais trop lent (P50={p50/1000:.1f}s > 12s) — rollback recommandé")
    else:
        print(f"  VERDICT ❌ : Score {pct}% insuffisant — rollback vers 7b")
    print(f"{'═'*80}\n")

    return {
        "model": model_name, "score_pct": pct,
        "success": success, "total": total,
        "latency_p50_ms": p50, "latency_p95_ms": p95,
        "results": [asdict(r) for r in results],
    }

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model",  default="actif", help="Nom pour le rapport (7b ou 14b)")
    parser.add_argument("--save",   action="store_true")
    parser.add_argument("--quick",  action="store_true", help="T01-T10 seulement")
    parser.add_argument("--id",     default=None, help="Tester une seule question ex: T09")
    args = parser.parse_args()

    questions = QUESTIONS
    if args.quick: questions = questions[:10]
    if args.id:    questions = [q for q in questions if q[0] == args.id]

    print(f"Connexion à {BASE_URL}...")
    token = get_token()
    print(f"Authentifié ✅ — {len(questions)} question(s) — modèle déclaré: {args.model}\n")

    results = []
    for i, (qid, question, category, difficulty, tour2) in enumerate(questions, 1):
        print(f"[{i:02d}/{len(questions):02d}] {qid} {question[:55]}", end="", flush=True)
        r = run_question(qid, question, category, difficulty, tour2, token)
        ok = "✅" if r.sql_success else "❌"
        print(f"  {ok} {r.latency_ms/1000:.1f}s")
        results.append(r)

    summary = print_report(results, args.model)

    if args.save:
        fname = f"/tmp/benchmark_{args.model}_{int(time.time())}.json"
        with open(fname, "w") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"Résultats sauvegardés : {fname}\n")

if __name__ == "__main__":
    main()
