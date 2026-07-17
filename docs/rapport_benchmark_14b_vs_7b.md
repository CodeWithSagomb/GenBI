# Rapport d'expérimentation — qwen2.5-coder:14b vs 7b

**Date :** 20 juin 2026 | **Système :** RuwaGenBI | **Matériel :** Apple M4 Pro 24 GB RAM

---

## Contexte

Le modèle actif en production est `qwen2.5-coder:7b` (score 100% sur la batterie de 10 questions). L'objectif de l'expérience était de déterminer si `qwen2.5-coder:14b` — modèle de même famille, deux fois plus grand — apporte une amélioration mesurable sur la qualité SQL ou la profondeur des analyses, au prix d'une latence plus élevée.

---

## Méthodologie

**Outil :** `test_compare_14b.py` — script de benchmark automatisé, 20 questions couvrant :
- 4 niveaux de difficulté : `easy` / `medium` / `hard` / `very_hard`
- 10 catégories fonctionnelles : simple, join, group_by, aggregation, join_filter, stocks, ruptures, purchases, multiturn, anti_join
- 2 questions multi-tour (T17, T18) avec vérification de la cohérence conversationnelle

**Critères de jugement définis avant le test :**
- Garder 14b si score ≥ 96% ET P50 < 12s
- Rollback si score < 93% OU P50 > 15s

**Protocole :**
1. Baseline 7b sur le système en production (sans changement)
2. Pull du modèle 14b (~9.0 GB)
3. Modification `.env` : `OLLAMA_MODEL=qwen2.5-coder:14b`, timeouts ajustés (90s / 70s)
4. Restart backend, benchmark identique
5. Comparaison objective, décision, rollback si nécessaire

---

## Résultats

| Métrique | qwen2.5-coder:7b | qwen2.5-coder:14b | Δ |
|---|---|---|---|
| Score SQL global | **20/20 (100%)** | 20/20 (100%) | = |
| easy (2 questions) | 2/2 | 2/2 | = |
| medium (7 questions) | 7/7 | 7/7 | = |
| hard (8 questions) | 8/8 | 8/8 | = |
| very_hard (3 questions) | 3/3 | 3/3 | = |
| Multi-tour T17 (Tour 2) | ✅ 13.0s | ✅ 33.5s | +2.6× |
| Multi-tour T18 (Tour 2) | ✅ 11.8s | ✅ 24.2s | +2.1× |
| **Latence P50** | **7.4s** | **15.3s** | **+2.1×** |
| **Latence P95** | **12.1s** | **35.0s** | **+2.9×** |
| Pire cas (T09 — stocks) | 9.1s | 35.0s | +3.8× |

---

## Analyse

**Qualité identique.** Les deux modèles génèrent un SQL valide et exécutable sur la totalité des 20 questions. Le 14b ne corrige aucune des erreurs que le 7b ferait — parce que le 7b n'en fait aucune. Le prompt v3 (12 règles, tableau QUESTION→TABLE) est suffisamment précis pour que le modèle plus grand n'apporte aucune valeur supplémentaire.

**Latence significativement dégradée.** Le goulot n'est pas la qualité de raisonnement mais le débit de tokens (tokens/s). Sur M4 Pro, le 14b génère environ 2× moins de tokens par seconde que le 7b. Cet effet est amplifié sur les requêtes complexes (JOIN multiples, anti-join) qui produisent des requêtes SQL plus longues.

**Explication physique.** `qwen2.5-coder:14b` en Q4_K_M occupe ~9.4 GB de poids + ~4-6 GB de KV cache et d'overhead runtime, soit ~14-16 GB de RAM unifiée active. Sur 24 GB, la marge est suffisante pour éviter le swap — mais le débit de lecture des poids en mémoire est mécaniquement plus lent que pour 7b (~4.7 GB).

---

## Décision

**Rollback vers `qwen2.5-coder:7b`.** Le critère de rollback est atteint : P50 = 15.3s > 15s. Aucun gain qualité ne justifie une latence 2× supérieure pour l'utilisateur final.

Le modèle 14b reste installé localement (`ollama list`) et peut être réactivé en une ligne si le contexte change (ex. questions plus ambiguës, schéma DB étendu à 50+ tables, ou machine plus puissante).

---

## État final du système

```
OLLAMA_MODEL=qwen2.5-coder:7b   ← production
LLM_SQL_TIMEOUT=60s
LLM_INSIGHT_TIMEOUT=45s
Score benchmark : 20/20 (100%) | P50 : 7.4s | P95 : 12.1s
```

---

## Fichiers liés

- Script benchmark : `test_compare_14b.py` (racine du projet)
- Résultats bruts 7b : `/tmp/benchmark_7b_1781977825.json`
- Résultats bruts 14b : `/tmp/benchmark_14b_1781978367.json`
