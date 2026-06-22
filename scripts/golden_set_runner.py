#!/usr/bin/env python3
"""
Runner du golden set — 50 questions métier avec validation automatique.

Usage:
    python3 scripts/golden_set_runner.py [--pharmacy EMAIL] [--category CAT] [--fail-fast]

Exemples:
    python3 scripts/golden_set_runner.py
    python3 scripts/golden_set_runner.py --category finance
    python3 scripts/golden_set_runner.py --fail-fast
    make golden
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

# Ajoute scripts/ au path pour importer golden_set
sys.path.insert(0, str(Path(__file__).parent))
from golden_set import GOLDEN_SET

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL   = "http://localhost:8000"
PHARMACY   = "bourguiba@pharma.sn"
PASSWORD   = "test123"
LANGUAGE   = "fr"

ANSI = {
    "green":  "\033[92m",
    "red":    "\033[91m",
    "yellow": "\033[93m",
    "cyan":   "\033[96m",
    "bold":   "\033[1m",
    "reset":  "\033[0m",
}
def c(color, text): return f"{ANSI[color]}{text}{ANSI['reset']}"


# ── Auth ──────────────────────────────────────────────────────────────────────
def get_token(email: str = PHARMACY, password: str = PASSWORD) -> str:
    r = requests.post(f"{BASE_URL}/api/v1/auth/login",
                      json={"email": email, "password": password}, timeout=10)
    r.raise_for_status()
    return r.json()["access_token"]


# ── Checks ────────────────────────────────────────────────────────────────────
def run_checks(q_def: dict, sub: dict) -> list[dict]:
    """Retourne la liste des checks avec résultat pass/fail."""
    checks  = q_def.get("checks", {})
    sql     = sub.get("sql", "").upper()
    rows    = sub.get("rows", [])
    row_count = sub.get("row_count", 0)
    viz     = sub.get("viz_hint")
    insight = sub.get("insight", "")
    results = []

    def add(name, passed, detail=""):
        results.append({"name": name, "passed": passed, "detail": detail})

    # sql_must_contain
    for kw in checks.get("sql_must_contain", []):
        ok = kw.upper() in sql
        add(f"sql_has:{kw}", ok, "" if ok else f"'{kw}' absent du SQL")

    # sql_must_not_contain
    for kw in checks.get("sql_must_not_contain", []):
        ok = kw.upper() not in sql
        add(f"sql_no:{kw}", ok, "" if ok else f"'{kw}' présent dans le SQL (interdit)")

    # row_count exact
    if "row_count" in checks:
        expected = checks["row_count"]
        ok = row_count == expected
        add("row_count", ok, "" if ok else f"attendu {expected}, reçu {row_count}")

    # row_count_min / max
    if "row_count_min" in checks:
        ok = row_count >= checks["row_count_min"]
        add("row_count_min", ok, "" if ok else f"< {checks['row_count_min']} lignes")
    if "row_count_max" in checks:
        ok = row_count <= checks["row_count_max"]
        add("row_count_max", ok, "" if ok else f"> {checks['row_count_max']} lignes")

    # value_range
    if "value_range" in checks and rows:
        vr  = checks["value_range"]
        col = vr.get("col", 0)
        try:
            val = float(rows[0][col])
            ok  = vr["min"] <= val <= vr["max"]
            add("value_range", ok,
                "" if ok else f"valeur {val:,.0f} hors plage [{vr['min']:,.0f}–{vr['max']:,.0f}]")
        except (IndexError, TypeError, ValueError) as e:
            add("value_range", False, f"impossible de lire la valeur: {e}")

    # viz_hint
    if "viz_hint" in checks:
        expected = checks["viz_hint"]
        ok = viz == expected
        add("viz_hint", ok, "" if ok else f"attendu '{expected}', reçu '{viz}'")

    # insight_forbidden
    for word in checks.get("insight_forbidden", []):
        ok = word.lower() not in insight.lower()
        add(f"insight_no:{word}", ok,
            "" if ok else f"'{word}' trouvé dans l'insight")

    return results


# ── Runner ────────────────────────────────────────────────────────────────────
def run_golden_set(
    category_filter: str | None = None,
    fail_fast: bool = False,
    pharmacy: str = PHARMACY,
) -> dict:
    token   = get_token(pharmacy)
    headers = {"Authorization": f"Bearer {token}"}
    questions = [q for q in GOLDEN_SET
                 if category_filter is None or q["category"] == category_filter]

    results   = []
    passed    = 0
    failed    = 0
    start_all = time.time()

    # En-tête
    cat_label = f" [{category_filter}]" if category_filter else ""
    print(f"\n{c('bold', '🏥  RuwaGenBI — Golden Set')} {c('cyan', f'{len(questions)} questions{cat_label}')}\n")
    header = f"{'ID':<8} {'Catégorie':<13} {'Question':<52} {'Checks':>6} {'ms':>5}  Verdict"
    print(header)
    print("─" * 100)

    for q_def in questions:
        qid      = q_def["id"]
        question = q_def["question"]
        t0       = time.time()
        check_results = []
        sub = {}
        error = None

        try:
            r = requests.post(
                f"{BASE_URL}/api/v1/analyse",
                json={"question": question, "language": LANGUAGE},
                headers=headers,
                timeout=90,
            )
            elapsed = int((time.time() - t0) * 1000)
            data = r.json()

            if r.status_code != 200:
                error = f"HTTP {r.status_code}"
            else:
                subs = data.get("sub_analyses", [])
                sub  = subs[0] if subs else {}
                check_results = run_checks(q_def, sub)

        except Exception as e:
            elapsed = int((time.time() - t0) * 1000)
            error   = str(e)[:60]

        if error:
            check_results = [{"name": "request", "passed": False, "detail": error}]

        all_passed = all(c["passed"] for c in check_results)
        n_pass = sum(1 for c in check_results if c["passed"])
        n_total = len(check_results)

        if all_passed:
            passed += 1
            verdict = c("green", f"✅  {n_pass}/{n_total}")
        else:
            failed += 1
            verdict = c("red",   f"❌  {n_pass}/{n_total}")

        q_short = question[:50] + ("…" if len(question) > 50 else "")
        print(f"{qid:<8} {q_def['category']:<13} {q_short:<52} {n_pass:>3}/{n_total:<2} {elapsed:>5}ms  {verdict}")

        # Détail des échecs
        for chk in check_results:
            if not chk["passed"]:
                print(f"         {c('yellow', '↳')} {chk['name']}: {chk['detail']}")

        results.append({
            "id": qid, "category": q_def["category"], "question": question,
            "elapsed_ms": elapsed, "passed": all_passed,
            "checks": check_results, "sub": {
                "sql":       sub.get("sql", ""),
                "row_count": sub.get("row_count"),
                "viz_hint":  sub.get("viz_hint"),
                "insight":   sub.get("insight", ""),
            }
        })

        if fail_fast and not all_passed:
            print(f"\n{c('red', '⛔  --fail-fast : arrêt sur premier échec')}")
            break

    total_elapsed = int((time.time() - start_all) * 1000)

    # ── Résumé ────────────────────────────────────────────────────────────────
    total = passed + failed
    pct   = int(100 * passed / total) if total else 0
    color = "green" if pct >= 90 else ("yellow" if pct >= 70 else "red")

    print("\n" + "═" * 100)
    print(f"\n  {c('bold', 'RÉSULTAT')}  {c(color, f'{passed}/{total}')}  ({pct}%)  "
          f"— temps total : {total_elapsed / 1000:.1f}s\n")

    if failed:
        print(f"  {c('red', '❌ Questions en échec :')}")
        for r in results:
            if not r["passed"]:
                fails = [ch["name"] for ch in r["checks"] if not ch["passed"]]
                print(f"     {r['id']:<8} {r['question'][:55]}")
                print(f"              checks : {', '.join(fails)}")
        print()

    # Par catégorie
    categories = sorted({r["category"] for r in results})
    print(f"  {'Catégorie':<15} {'Score'}")
    print(f"  {'─'*30}")
    for cat in categories:
        cat_res = [r for r in results if r["category"] == cat]
        p = sum(1 for r in cat_res if r["passed"])
        t = len(cat_res)
        col = "green" if p == t else ("yellow" if p >= t * 0.8 else "red")
        print(f"  {cat:<15} {c(col, f'{p}/{t}')}")
    print()

    return {"passed": passed, "failed": failed, "total": total, "pct": pct, "results": results}


# ── Sauvegarde rapport JSON ────────────────────────────────────────────────────
def save_report(data: dict, output_dir: str = "reports") -> str:
    Path(output_dir).mkdir(exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{output_dir}/golden_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    return path


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RuwaGenBI Golden Set Runner")
    parser.add_argument("--pharmacy", default=PHARMACY, help="Email du compte pharmacie")
    parser.add_argument("--category", default=None,
                        choices=["finance", "produits", "stocks", "ruptures",
                                 "clients", "fournisseurs", "operationnel"],
                        help="Filtrer par catégorie")
    parser.add_argument("--fail-fast", action="store_true",
                        help="Arrêter au premier échec")
    parser.add_argument("--save", action="store_true",
                        help="Sauvegarder le rapport JSON dans reports/")
    args = parser.parse_args()

    report = run_golden_set(
        category_filter=args.category,
        fail_fast=args.fail_fast,
        pharmacy=args.pharmacy,
    )

    if args.save:
        path = save_report(report)
        print(f"  💾 Rapport sauvegardé : {path}\n")

    sys.exit(0 if report["failed"] == 0 else 1)
