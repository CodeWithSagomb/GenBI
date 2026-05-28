# Formation : Spec-Driven Development avec Spec Kit — Adapté à GenBI

> Source analysée : https://github.com/github/spec-kit (107k ⭐ — 9 400 forks)

---

## 1. C'est quoi Spec Kit et pourquoi c'est révolutionnaire ?

Spec Kit est un toolkit open-source (GitHub, 2025) qui implémente le **Spec-Driven Development (SDD)** — une méthodologie qui inverse le développement traditionnel.

### Le problème qu'il résout

**Développement classique (vibe coding) :**
```
Idée floue → Claude code → Résultat imprévisible → Refactoring infini
```

**Spec-Driven Development :**
```
Constitution → Spec (QUOI) → Clarify → Plan (COMMENT) → Tasks → Implement
```

La spec devient l'artefact principal. L'IA implémente ce qui est défini, pas ce qu'elle interprète.

### Le résultat concret

- **Résultats prévisibles** : Claude implémente exactement ce qui est spécifié
- **Zéro ambiguïté** : les questions sont posées AVANT le code, pas pendant
- **Traçabilité** : chaque ligne de code est liée à une exigence
- **Indépendance des features** : chaque user story est livrable séparément

---

## 2. Les 7 étapes du workflow SDD

```
1. /speckit.constitution  → Principes fondateurs (non-négociables)
2. /speckit.specify       → Spécification de la feature (QUOI, PAS COMMENT)
3. /speckit.clarify       → Validation des ambiguïtés (max 3 questions)
4. /speckit.plan          → Stratégie d'implémentation technique
5. /speckit.tasks         → Découpage en tâches ordonnées
6. /speckit.analyze       → Vérification de cohérence entre artefacts
7. /speckit.implement     → Exécution phase par phase
```

Chaque commande est un **slash command Claude Code** — elle charge un template précis qui guide Claude avec une structure stricte.

---

## 3. Les 4 artefacts produits

### Constitution `.specify/memory/constitution.md`
Les règles non-négociables du projet. Tout code doit respecter la constitution.
- Versionnée sémantiquement (ex: `v1.2.0`)
- Amendable seulement avec justification documentée

### Spec `specs/[NNN]-[feature]/spec.md`
Le **QUOI** — décrit le besoin utilisateur, pas la technique.
- Écrit comme si l'IA n'existait pas
- Contient : User Stories prioritisées, Exigences fonctionnelles, Critères de succès mesurables
- INTERDIT : noms de frameworks, de langages, d'APIs

### Plan `specs/[NNN]-[feature]/plan.md`
Le **COMMENT** — décisions techniques déduites de la spec.
- Modèle de données, contrats d'interface, recherche de patterns

### Tasks `specs/[NNN]-[feature]/tasks.md`
La liste de tâches ordonnée avec dépendances explicites.
- Phases : Setup → Fondation (BLOQUANT) → User Story 1 → User Story 2 → ...
- `[P]` = exécutable en parallèle
- `[US1]` = appartient à la User Story 1

---

## 4. Adaptation à GenBI — Structure `.specify/`

```
GenBI/
├── CLAUDE.md
├── .specify/
│   ├── memory/
│   │   └── constitution.md       ← Principes non-négociables de GenBI
│   └── extensions.yml            ← Hooks optionnels (futur)
└── specs/
    ├── 001-dbt-semantic-layer/   ← Phase 2 : Couche sémantique dbt
    │   ├── spec.md
    │   ├── plan.md
    │   └── tasks.md
    ├── 002-backend-api/          ← Phase 3 : API FastAPI
    │   ├── spec.md
    │   ├── plan.md
    │   └── tasks.md
    ├── 003-frontend-chat/        ← Phase 4 : Interface de chat
    │   ├── spec.md
    │   ├── plan.md
    │   └── tasks.md
    └── 004-rag-feedback/         ← Phase 5 : RAG + feedback loop
        └── spec.md               ← (spec uniquement pour l'instant)
```

---

## 5. La Règle d'or : Spec = QUOI, Plan = COMMENT

### Ce qui appartient à la Spec (langage métier)

✅ "Le pharmacien peut demander le chiffre d'affaires du mois en langage naturel"
✅ "Le système répond en moins de 10 secondes"
✅ "La réponse montre le SQL généré pour la transparence"
✅ "Les données de patients ne quittent jamais le serveur local"

### Ce qui appartient au Plan (langage technique)

✅ "Utiliser dbt-core avec PostgreSQL en dialecte SQL"
✅ "Le LLM est qwen2.5-coder:7b via Ollama local"
✅ "L'endpoint FastAPI `/api/v1/chat` reçoit un POST JSON"
✅ "SQLGlot parse la requête pour détecter les non-SELECT"

### Ce qui est INTERDIT dans la Spec

❌ "Utiliser FastAPI avec async/await"
❌ "Stocker dans PostgreSQL avec psycopg2"
❌ "React state management avec useState"

---

## 6. Comment travailler avec SDD dans GenBI — Workflow pratique

### Avant de coder quoi que ce soit, appliquer ce processus :

```
1. Ouvrir Claude Code dans le dossier GenBI
2. Écrire la spec de la feature (ou charger le template spec.md)
3. Demander à Claude de clarifier les ambiguïtés (max 3)
4. Demander le plan technique
5. Demander la liste de tâches
6. Valider la cohérence (spec ↔ plan ↔ tasks)
7. Implémenter tâche par tâche
```

### Exemple concret pour la Phase 2 (dbt) :

**Étape 1 — Spec :** "Crée la spec pour la couche sémantique dbt qui transforme les données brutes de pharmacie en tables analytiques documentées pour l'IA."

**Étape 2 — Plan :** "Crée le plan technique pour la spec `specs/001-dbt-semantic-layer/spec.md` en suivant la constitution GenBI."

**Étape 3 — Tasks :** "Génère les tâches ordonnées à partir du plan, avec les dépendances explicites et les tâches parallélisables marquées [P]."

**Étape 4 — Implement :** "Commence l'implémentation de la Phase 1 (Setup) du fichier `specs/001-dbt-semantic-layer/tasks.md`."

---

## 7. Critères de succès — Ce qui change avec SDD

### Avant SDD (vibe coding)
- "Crée les modèles dbt" → Claude invente une structure
- Résultats incohérents entre sessions
- Impossible de savoir si c'est complet

### Avec SDD
- Spec définit exactement les 10 tables, leurs descriptions, les règles
- Plan définit les nommages, les tests, les matérialisations
- Tasks définit l'ordre d'exécution avec checkpoints testables
- Chaque tâche = une PR avec une traçabilité claire

---

## 8. Structure des critères de succès (règle Spec Kit)

Les critères de succès doivent être :
1. **Mesurables** : avec des métriques concrètes
2. **Agnostiques technologiquement** : pas de frameworks ou d'APIs
3. **Centrés utilisateur** : du point de vue du pharmacien
4. **Vérifiables** : sans connaître l'implémentation

**Bons exemples pour GenBI :**
- "Le pharmacien obtient une réponse à sa question en moins de 15 secondes"
- "95% des questions sur les ventes produisent un résultat correct"
- "Aucune donnée patient ne quitte le réseau local"
- "Le pharmacien voit le SQL généré pour valider la réponse"

**Mauvais exemples :**
- ❌ "Le LLM répond en moins de 5 secondes" (technique)
- ❌ "L'API FastAPI retourne un JSON 200" (implémentation)
- ❌ "dbt run s'exécute sans erreur" (outil interne)

---

## 9. Ce que Spec Kit nous apporte concrètement

| Problème GenBI | Solution SDD |
|---|---|
| "On ne sait pas exactement quoi coder ensuite" | La spec définit exactement le QUOI |
| "Claude part dans des directions non prévues" | Le plan cadre toutes les décisions techniques |
| "Impossible de reprendre là où on s'est arrêté" | Les tasks.md gardent l'état exact |
| "Les features sont interdépendantes et difficiles à isoler" | Chaque user story est indépendamment testable |
| "La constitution est dans nos têtes" | `.specify/memory/constitution.md` est la référence unique |

---

## 10. Les fichiers créés pour GenBI

Suite à cette formation, voici ce qui est mis en place :

| Fichier | Rôle |
|---|---|
| `.specify/memory/constitution.md` | Principes non-négociables de GenBI v1.0.0 |
| `specs/001-dbt-semantic-layer/spec.md` | Spec Phase 2 : couche dbt |
| `specs/001-dbt-semantic-layer/plan.md` | Plan technique Phase 2 |
| `specs/001-dbt-semantic-layer/tasks.md` | Tâches ordonnées Phase 2 |
| `specs/002-backend-api/spec.md` | Spec Phase 3 : API FastAPI |

Ces fichiers sont le **point de départ** — ils doivent être lus et validés avant tout développement.
