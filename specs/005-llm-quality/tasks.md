# Tasks — Phase 6 : Qualité LLM

**Dernière mise à jour** : 2026-06-04  
**Statut global** : 16 / 22 ✅

---

## Track 1 — Benchmark automatique

- [x] **T601** — Créer `tests/benchmark/` + `__init__.py` + `conftest_benchmark.py`
- [x] **T602** — Écrire les 30 paires `(question, sql_attendu)` dans `golden_questions.py`
- [x] **T603** — Implémenter `run_benchmark.py` : chat → execute → compare résultats
- [x] **T604** — Mesurer le score de départ (avant toute modification) — **26/30 (86 %)** documenté
- [x] **T605** — Identifier et catégoriser les échecs : Q11 (GROUP BY catégorie), Q17 (filtre date erroné), Q29 (filtre product_category manquant), Q30 (colonne therapeutic_group inexistante)

---

## Track 2 — Seed RAG

- [x] **T606** — Ajouter `seed_collection(client, pharmacy_id, examples)` dans `core/rag.py`
- [x] **T607** — 5 tests unitaires `tests/unit/test_rag_seed.py` — **5/5 PASS**
- [x] **T608** — Appeler `seed_collection` dans le lifespan `main.py` (best-effort, après init ChromaDB)
- [x] **T609** — Vérifier : ChromaDB non vide après redémarrage — pharmacy_1:20 pharmacy_2:30 pharmacy_3:30
- [x] **T610** — Re-mesurer après seed : score identique (RAG était silencieusement KO → fix api_base)

---

## Track 3 — Amélioration prompt

- [x] **T611** — Analyser les 4 échecs : GROUP BY catégorie / filtre date ruptures / product_category / therapeutic_class
- [x] **T612** — Créer `core/prompts/v2_sql_generation.txt` avec 4 corrections ciblées
- [x] **T613** — `SQL_PROMPT_VERSION = "v2_sql_generation"` dans `config.py` + `llm.py` configurable
- [x] **T614** — 3 tests unitaires prompt v1/v2 — **3/3 PASS** — ajoutés à `test_llm_prompt_builder.py`
- [x] **T615** — Re-mesurer benchmark avec prompt v2 — **30/30 (100 %)** ← score parfait
- [x] **T616** — Aucune itération nécessaire (100 % au premier essai)

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
| T1 — Benchmark | T601–T605 | Aucune | ✅ 26/30 (86%) de départ |
| T2 — Seed RAG | T606–T610 | T601 (golden questions) | ✅ ChromaDB peuplé + api_base fix |
| T3 — Prompt | T611–T616 | T604 (score de départ) | ✅ **30/30 (100%)** |
| T4 — Modèles | T617–T622 | T615 (score v2 établi) | ⏳ Optionnel — déjà à 100% |
| **Total** | **22 tâches** | | **16/22 ✅ (T4 optionnel)** |
