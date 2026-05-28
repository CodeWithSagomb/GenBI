# Formation : Développer GenBI avec Claude Code

Adaptation de l'article officiel Anthropic *"How Claude Code Works in Large Codebases"* aux besoins concrets du projet GenBI.

> Source : https://claude.com/blog/how-claude-code-works-in-large-codebases-best-practices-and-where-to-start

---

## La leçon fondamentale de l'article

> *"Le harness (l'écosystème de configuration autour du modèle) détermine les performances de Claude Code plus que le modèle lui-même."*

En clair : configurer correctement Claude Code pour GenBI nous donnera de bien meilleurs résultats que de simplement écrire de bons prompts. C'est ce que ce document met en place.

---

## Les 7 composants du Harness Claude Code

L'article décrit 7 composants. Voici leur traduction concrète pour GenBI :

---

### Composant 1 : CLAUDE.md — La mémoire permanente du projet

**Ce que dit l'article :** Le fichier `CLAUDE.md` se charge automatiquement à chaque session. Il doit contenir uniquement les "pointeurs et gotchas critiques", pas tout documenter dedans (cela dégrade les performances).

**Ce qu'on a fait pour GenBI :**
Le fichier `CLAUDE.md` à la racine a été créé avec :
- Le contexte produit en une phrase
- La table des ports de tous les services
- Les commandes `make` essentielles
- Les **5 gotchas critiques** (Ollama natif, user read-only, SQLGlot, manifest.json, connexion Airflow)
- L'état d'avancement par phase
- Les conventions de code

**Règle d'or :** Ne pas transformer CLAUDE.md en documentation complète. Si quelque chose appartient à `guide_meilleures_pratiques.md`, le laisser là. CLAUDE.md pointe vers les autres fichiers.

**Structure CLAUDE.md par couche recommandée :**
```
CLAUDE.md (racine)          ← Vue d'ensemble, gotchas globaux
airflow/CLAUDE.md           ← Conventions DAGs, connexions Airflow
dbt_project/CLAUDE.md       ← Nommage dbt, commandes, tests obligatoires
genbi_backend/CLAUDE.md     ← Architecture FastAPI, sécurité SQL
genbi_frontend/CLAUDE.md    ← Composants React, hooks, design system
```

Quand Claude Code travaille dans `genbi_backend/`, il charge automatiquement :
`CLAUDE.md (racine)` → `genbi_backend/CLAUDE.md`

→ **Action immédiate :** Créer un `CLAUDE.md` dans chaque sous-dossier au fur et à mesure du développement des phases.

---

### Composant 2 : Hooks — Automatiser les comportements répétitifs

**Ce que dit l'article :** Les hooks sont des scripts déclenchés par des événements clés (avant/après une action de Claude). Ils automatisent les comportements cohérents et capturent les apprentissages de session.

**Hooks à mettre en place pour GenBI :**

#### Hook post-édition : validation SQL automatique
Après chaque modification d'un fichier SQL dbt, lancer `dbt compile` pour vérifier la syntaxe :

```json
// .claude/settings.json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "if echo '$CLAUDE_TOOL_INPUT' | grep -q 'dbt_project.*\\.sql'; then cd dbt_project && dbt compile --select $(basename $CLAUDE_TOOL_INPUT .sql) 2>&1 | tail -5; fi"
          }
        ]
      }
    ]
  }
}
```

#### Hook post-édition : lint Python automatique
Après chaque modification d'un fichier Python backend :
```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "if echo '$CLAUDE_TOOL_INPUT' | grep -q 'genbi_backend.*\\.py'; then cd genbi_backend && python -m py_compile $(basename $CLAUDE_TOOL_INPUT) && echo '✓ Syntax OK'; fi"
    }
  ]
}
```

**Principe :** Les hooks remplacent l'instruction "n'oublie pas de valider la syntaxe à chaque fois" — Claude ne peut pas oublier ce que le système exécute automatiquement.

---

### Composant 3 : Skills — Instructions spécialisées chargées à la demande

**Ce que dit l'article :** Les skills sont des instructions packagées pour des types de tâches spécifiques. Ils évitent de surcharger le contexte en ne chargeant l'expertise spécialisée que quand c'est pertinent.

**Skills à créer pour GenBI :**

#### Skill : Créer un modèle dbt
Quand on demande "crée le modèle staging pour les ventes", Claude charge automatiquement les règles de nommage, la structure YAML obligatoire, et les tests à ajouter.

#### Skill : Créer un endpoint FastAPI
Charge la structure `router.py + service.py + schemas.py` par domaine, les règles async, le pattern de dependency injection.

#### Skill : Générer un prompt Text-to-SQL
Charge la structure XML du prompt (schema → few-shot → question), les règles de sécurité, le format de sortie structuré attendu.

**Comment les créer :**
```
.claude/
└── skills/
    ├── dbt-model.md       ← Instructions pour créer un modèle dbt
    ├── fastapi-endpoint.md ← Instructions pour créer un endpoint
    └── text-to-sql.md     ← Instructions pour le prompt engineering SQL
```

---

### Composant 4 : Permissions — Protéger le projet

**Ce que dit l'article :** Utiliser `.claude/settings.json` avec des règles `permissions.deny` pour éliminer les fichiers générés et les artefacts de build des actions de Claude.

**Ce qu'on a configuré pour GenBI :**

```json
// .claude/settings.json (déjà créé)
{
  "permissions": {
    "deny": [
      "Bash(rm -rf *)",          // Pas de suppression récursive
      "Bash(docker compose down -v*)", // Pas de suppression de volumes
      "Bash(git push --force*)", // Pas de force push
      "Bash(git reset --hard*)", // Pas de reset destructif
      "Bash(DROP TABLE*)",       // Pas de suppression de tables
      "Bash(DELETE FROM*)"       // Pas de delete direct en DB
    ]
  }
}
```

**À ajouter :** Exclure les dossiers générés des actions de Claude :
```json
{
  "permissions": {
    "deny": [
      "Write(dbt_project/target/**)",      // Généré par dbt
      "Write(dbt_project/dbt_packages/**)", // Dépendances dbt
      "Write(genbi_frontend/node_modules/**)", // Dépendances npm
      "Write(airflow/logs/**)"             // Logs Airflow
    ]
  }
}
```

---

### Composant 5 : LSP (Language Server Protocol) — Navigation précise dans le code

**Ce que dit l'article :** Le LSP permet une navigation au niveau des symboles (comme "go to definition" dans un IDE), particulièrement utile pour les codebases multi-langages.

**Application pour GenBI :**
GenBI est multi-langages : Python (backend), JavaScript/JSX (frontend), SQL (dbt), YAML (configuration).

**Configuration VS Code recommandée :**
- **Python LSP** : Pylance (déjà inclus dans VS Code Python extension)
- **Jinja/SQL LSP** : Extension "dbt Power User" pour VS Code
- **JavaScript LSP** : Volar ou ESLint

Avec le LSP actif, quand on demande à Claude Code "trouve toutes les utilisations de `get_readonly_db`", il navigue par symbole plutôt que par grep — beaucoup plus précis.

---

### Composant 6 : MCP Servers — Connecter Claude aux outils internes

**Ce que dit l'article :** Les MCP Servers connectent Claude aux APIs internes et aux sources de données. Les équipes avancées exposent la recherche structurée comme des outils appelables.

**MCP Servers à configurer pour GenBI :**

#### MCP PostgreSQL (prioritaire)
Permet à Claude de requêter directement la base de données pour explorer le schéma ou vérifier les données sans quitter la session.

```json
// Ajouter dans .claude/settings.json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://genbi_readonly:genbi_secure_readonly_123@localhost:5432/genbi"]
    }
  }
}
```

Avec ce MCP, on peut demander : "Montre-moi les 5 produits les plus vendus ce mois" — et Claude interroge directement la DB pour valider les modèles dbt.

#### MCP Filesystem (utile pour dbt)
Expose `dbt_project/target/manifest.json` comme une ressource lisible structurée.

---

### Composant 7 : Subagents — Exploration parallèle sans saturer le contexte

**Ce que dit l'article :** Les subagents sont des instances Claude isolées qui gèrent l'exploration séparément de l'édition. Ils permettent le travail en parallèle et préviennent l'épuisement de la fenêtre de contexte.

**Quand utiliser les subagents dans GenBI :**

| Tâche | Approche |
|---|---|
| "Explore le schéma dbt et implémente les 10 modèles staging" | Subagent Explore → résultats → édition dans le thread principal |
| "Refactorise le backend ET crée les tests" | 2 subagents en parallèle |
| "Analyse le manifest.json et génère le parser" | Subagent pour lire, thread principal pour écrire |
| Petite modification d'un fichier connu | Thread principal directement |

**Règle pratique :** Si la tâche nécessite de lire plus de 5 fichiers avant d'écrire, utiliser un subagent d'exploration d'abord.

---

## Workflow de Développement Recommandé pour GenBI

### Comment aborder chaque session de travail

```
1. Claude charge automatiquement CLAUDE.md (contexte projet + état)
2. Spécifier la tâche précisément avec le contexte nécessaire
3. Pour les tâches d'exploration large → spawn un subagent Explore
4. Vérifier les changements avant de valider (make ps, dbt test, etc.)
5. Si une règle manque dans CLAUDE.md → l'ajouter immédiatement
```

### Formulation des tâches (ce qui change tout)

**Moins efficace :**
> "Crée les modèles dbt"

**Plus efficace :**
> "Crée les 10 modèles staging dans `dbt_project/models/staging/raw/` en suivant les conventions du `guide_meilleures_pratiques.md` (préfixe `stg_raw__`, matérialisé en view, pas de jointures). Commence par `stg_raw__sales.sql` et son fichier YAML avec description de chaque colonne."

**Pourquoi :** Claude Code cherche dans le code en live — plus la tâche est précise, moins il navigue à l'aveugle.

### Garder CLAUDE.md vivant

Après chaque session significative, mettre à jour :
- L'état d'avancement des phases
- Les nouveaux gotchas découverts
- Les nouvelles commandes utiles

Revoir CLAUDE.md tous les 3-6 mois ou après une mise à jour majeure de Claude — les instructions optimisées pour un ancien modèle peuvent contraindre les nouveaux.

---

## Ce qui est déjà en place dans GenBI

| Composant | Status | Fichier |
|---|---|---|
| CLAUDE.md racine | ✅ Créé | `CLAUDE.md` |
| settings.json (permissions) | ✅ Créé | `.claude/settings.json` |
| CLAUDE.md sous-dossiers | ⏳ À créer au fil du dev | `airflow/`, `dbt_project/`, `genbi_backend/`, `genbi_frontend/` |
| Hooks (post-édition) | ⏳ À configurer | `.claude/settings.json` |
| Skills (dbt, FastAPI, SQL) | ⏳ À créer | `.claude/skills/` |
| MCP PostgreSQL | ⏳ Recommandé | `.claude/settings.json` |
| MCP Filesystem | ⏳ Optionnel | `.claude/settings.json` |

---

## Résumé : Les 5 choses à retenir

1. **CLAUDE.md > Prompts** — Ce qui est dans CLAUDE.md est chargé automatiquement à chaque session. Un bon CLAUDE.md vaut mieux que 10 prompts répétés.

2. **Gotchas critiques en premier** — Les 5 gotchas du projet (Ollama natif, user read-only, SQLGlot, manifest.json, Airflow connexion) sont dans CLAUDE.md. Claude ne les oubliera plus.

3. **Permissions deny = garde-fous** — Configurer ce que Claude ne peut PAS faire (rm -rf, force push, DROP TABLE) dans settings.json avant de commencer à coder sérieusement.

4. **Tâches précises = meilleurs résultats** — Inclure le fichier cible, les conventions à respecter, et l'exemple attendu dans chaque instruction.

5. **Subagent pour l'exploration, thread principal pour l'édition** — Ne pas laisser l'exploration épuiser la fenêtre de contexte avant d'avoir écrit une ligne.
