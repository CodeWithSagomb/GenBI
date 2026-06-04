# Spec — Phase 6 : Qualité LLM

**Statut** : 🔄 En cours  
**Créée** : 2026-06-04  
**Objectif** : Mesurer, améliorer et valider la précision du Text-to-SQL sur des questions pharmaceutiques réelles.

---

## Contexte

À l'issue de Phase 5, le LLM génère du SQL exploitable sur ~15 questions validées manuellement. Deux bugs de prompt ont été corrigés pendant la préparation démo (filtre `sale_month` figé, colonnes `missed_month` manquantes). Le RAG ChromaDB est opérationnel mais **vide** — aucun exemple n'a encore été indexé. Il n'existe aucun benchmark automatique de qualité.

**Problème** : sans mesure, on améliore à l'aveugle.

---

## Périmètre

| Track | Objectif | Livrable |
|---|---|---|
| T1 — Benchmark | Mesurer la précision actuelle | 30 questions golden + score pytest |
| T2 — Seed RAG | Activer le few-shot dès le démarrage | 15 exemples dans ChromaDB au boot |
| T3 — Prompt | Corriger les échecs identifiés par T1 | Prompt v2 + re-mesure |
| T4 — Modèles | Comparer qwen2.5-coder:7b vs alternatives | Rapport benchmark multi-modèle |

**Objectif cible** : passer de ? / 30 à ≥ 25 / 30 (83 % de précision).

---

## Track 1 — Benchmark automatique

### Principe
Un fichier `tests/benchmark/golden_questions.py` contient 30 paires `(question, sql_attendu)`. Le script exécute chaque question via `/api/v1/chat`, compare le SQL généré au SQL de référence, exécute les deux et compare les résultats.

### Critère de succès
Deux niveaux de validation :
- **Niveau 1 — Exécution** : le SQL généré s'exécute sans erreur et retourne des données (pas de 0 lignes quand on en attend).
- **Niveau 2 — Résultat** : les données retournées sont identiques au SQL de référence (même colonnes, même ordre de grandeur).

### Catégories de questions (30 total)
| Catégorie | Nb | Exemples |
|---|---|---|
| CA simple (mois, total, période) | 6 | "CA mars 2026", "CA par mois", "CA total" |
| Produits (top, quantité, CA) | 6 | "5 plus vendus", "10 plus rentables" |
| Ruptures de stock | 5 | "produits en rupture", "ruptures par mois", "top ruptures" |
| Clients (type, fidélité, CA) | 4 | "CA par type client", "nb clients" |
| Statistiques globales | 5 | "nb ventes total", "montant moyen", "meilleur mois" |
| Jointures complexes | 4 | "CA antibiotiques", "produits par assurés" |

---

## Track 2 — Seed RAG

### Principe
Au démarrage (`lifespan`), si la collection ChromaDB d'une pharmacie est vide, injecter les exemples golden de Track 1 via `index_example()`. Ces exemples sont neutres (pas liés à une pharmacie spécifique) et servent de base few-shot universelle.

### Implémentation
- `core/rag.py` : nouvelle fonction `seed_collection(client, pharmacy_id, examples)`
- `main.py` lifespan : appel best-effort après initialisation ChromaDB
- Les exemples proviennent directement du fichier golden de T1

---

## Track 3 — Amélioration prompt

### Principe
Analyser les questions qui échouent au benchmark T1. Identifier les patterns d'échec :
- Mauvaise table utilisée
- Jointure incorrecte
- Filtre temporel erroné
- Colonne inexistante

Corriger le prompt `v1_sql_generation.txt` → `v2_sql_generation.txt`. Re-mesurer.

### Versionning
- `core/prompts/v1_sql_generation.txt` — version actuelle (conservée)
- `core/prompts/v2_sql_generation.txt` — version améliorée
- `config.py` : `SQL_PROMPT_VERSION: str = "v2_sql_generation"` (configurable)

---

## Track 4 — Comparaison modèles (optionnel)

### Candidats
| Modèle | Taille | Spécialité |
|---|---|---|
| `qwen2.5-coder:7b` | 4.7 GB | Actuel — code/SQL |
| `llama3.2:3b` | 2.0 GB | Rapide, généraliste |
| `mistral:7b` | 4.1 GB | Raisonnement |
| `deepseek-coder:6.7b` | 3.8 GB | Spécialisé code |

### Critère de choix
Score benchmark T1 ≥ 25/30 **ET** temps de réponse médian ≤ 8s.

---

## Contraintes

- Tests benchmark : s'exécutent dans Docker (`docker exec genbi_backend`)
- Ne pas modifier les 114 tests existants (ne pas régresser)
- Prompt v1 conservé — v2 activable via `config.py` sans redéploiement
- RAG seed : best-effort (erreur non bloquante au démarrage)

---

## Définition of Done

- [ ] Score benchmark mesuré avant et après
- [ ] ≥ 25 / 30 questions correctes (niveau 1 au minimum)
- [ ] RAG non vide au premier démarrage
- [ ] Prompt versionné (v1 → v2)
- [ ] 114 tests existants toujours PASS
