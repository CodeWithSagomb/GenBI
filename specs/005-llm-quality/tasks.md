# Tasks — Phase 6 : Qualité LLM

**Dernière mise à jour** : 2026-06-04  
**Statut global** : 0 / 22 ✅

---

## Track 1 — Benchmark automatique

- [ ] **T601** — Créer `tests/benchmark/` + `__init__.py` + `conftest_benchmark.py`
- [ ] **T602** — Écrire les 30 paires `(question, sql_attendu)` dans `golden_questions.py`
- [ ] **T603** — Implémenter `run_benchmark.py` : chat → execute → compare résultats
- [ ] **T604** — Mesurer le score de départ (avant toute modification) — documenter dans `DASHBOARD.md`
- [ ] **T605** — Identifier et catégoriser les échecs (pattern : mauvaise table, jointure, filtre…)

---

## Track 2 — Seed RAG

- [ ] **T606** — Ajouter `seed_collection(client, pharmacy_id, examples)` dans `core/rag.py`
- [ ] **T607** — 5 tests unitaires `tests/unit/test_rag_seed.py`
- [ ] **T608** — Appeler `seed_collection` dans le lifespan `main.py` (best-effort, après init ChromaDB)
- [ ] **T609** — Vérifier : ChromaDB non vide après redémarrage du container
- [ ] **T610** — Re-mesurer le score benchmark après seed (T1 niveau comparaison)

---

## Track 3 — Amélioration prompt

- [ ] **T611** — Analyser les échecs T604/T605 — liste des patterns à corriger
- [ ] **T612** — Créer `core/prompts/v2_sql_generation.txt` avec corrections ciblées
- [ ] **T613** — Ajouter `SQL_PROMPT_VERSION` dans `config.py` + `llm.py` lit la version configurable
- [ ] **T614** — 3 tests unitaires : prompt v1 vs v2 chargés selon config
- [ ] **T615** — Re-mesurer benchmark avec prompt v2 — documenter delta (ex : 18/30 → 24/30)
- [ ] **T616** — Itérer sur v2 si score < 25/30 (max 2 itérations)

---

## Track 4 — Comparaison modèles (optionnel)

- [ ] **T617** — `ollama pull` du modèle challenger retenu (deepseek-coder:6.7b ou mistral:7b)
- [ ] **T618** — Adapter `run_benchmark.py` pour paramètre `--model`
- [ ] **T619** — Lancer benchmark sur modèle challenger — noter score + temps médian
- [ ] **T620** — Comparer : qwen2.5-coder:7b vs challenger (score + latence)
- [ ] **T621** — Mettre à jour `config.py` si le challenger est meilleur
- [ ] **T622** — Documenter la décision dans `DASHBOARD.md`

---

## Récapitulatif

| Track | Tâches | Dépendances | Statut |
|---|---|---|---|
| T1 — Benchmark | T601–T605 | Aucune | ⏳ |
| T2 — Seed RAG | T606–T610 | T601 (golden questions) | ⏳ |
| T3 — Prompt | T611–T616 | T604 (score de départ) | ⏳ |
| T4 — Modèles | T617–T622 | T615 (score v2 établi) | ⏳ |
| **Total** | **22 tâches** | | **0/22 ✅** |
