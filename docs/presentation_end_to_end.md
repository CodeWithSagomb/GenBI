# RuwaGenBI, présentation technique end-to-end

Public : technique (devs/ingénieurs) · Durée cible : 15-20 min · 18 sections

Chaque section ci-dessous correspond à un panneau du diaporama (`docs/presentation/index.html`).
Minutage indicatif entre parenthèses, total autour de 17 min hors questions.

---

## 1. Titre (0:30)
**RuwaGenBI** : BI générative pour pharmacies, 100% locale.

Accroche d'ouverture : *"Un pharmacien tape une question en français. Neuf étapes plus tard, il a un graphique et une phrase, sans qu'aucune donnée n'ait quitté la machine, et sans qu'un développeur ait écrit la requête à l'avance."*

## 2. Le problème (1:00)
La BI classique (Metabase, Tableau, etc.) fonctionne par dashboards pré-construits :
```
besoin métier → analyste écrit le SQL → dashboard publié → utilisateur consulte
     ↑                                                              │
     └──────── nouvelle question non couverte ? ────────────────────┘
```
Limite structurelle : l'utilisateur ne peut jamais poser une question qui n'a pas été anticipée. Chaque nouvelle question suppose un ticket, puis un cycle de développement.

Point de preuve dans le projet même : le Dashboard React (`useDashboard.js`) contient 6 requêtes SQL pré-écrites. C'est de la BI classique, juste avec une interface moderne.

## 3. La proposition (1:00)
Remplacer "écrire le SQL à l'avance" par "générer le SQL à la volée", en langage naturel, pour n'importe quelle question dans le périmètre du schéma.

Le vrai piège à nommer ici, celui qui vient à l'esprit du public : un LLM qui génère du SQL peut halluciner, se tromper de colonne, halluciner un résultat. Le reste de la présentation, c'est comment on construit la confiance autour de cette imprévisibilité.

## 4. Vue d'ensemble architecture (1:00)
```
React (Vite)  ⇄  FastAPI  ⇄  Ollama (natif macOS, qwen2.5-coder:7b)
                     ⇓
              PostgreSQL 16 (RLS actif)
                     ⇑
              dbt (raw → staging → marts)
```
Point clé à appuyer : Ollama tourne nativement sur la machine, pas dans un container, donc zéro appel réseau externe pour la génération SQL et insight. C'est la base de l'argument "zéro fuite de données".

## 5. La couche de données (1:00)
3 couches dbt : `raw` (brut, jamais modifié), puis `staging` (vues, nettoyage), puis `marts` (tables, dénormalisées pour le LLM). 19 modèles au total (10 staging, 9 marts).

Isolation multi-pharmacie : pas un `WHERE pharmacy_id = ?` dans le code Python, mais une policy RLS PostgreSQL, appliquée via un post-hook dbt sur chaque table de faits. Garantie structurelle : même si le SQL généré par le LLM oublie un filtre, la fuite entre pharmacies est impossible.

## 6. Le pipeline en 9 étapes, vue d'ensemble (1:00)
Montrer le diagramme complet, annoncer qu'on zoome ensuite sur les points les plus intéressants (pas les 9 en détail, le temps manquerait).
```
question → RAG → filtrage du schéma → génération du SQL → validation
         → exécution + réparation automatique → vérification de cohérence → mise en forme
         → rédaction de l'insight → choix du graphique → réponse
```
Autour de 800 millisecondes de bout en bout sur la question de référence testée.

## 7. RAG et filtrage du schéma, réduire intelligemment le contexte (1:30)
Deux mécanismes distincts, même modèle d'embedding (`nomic-embed-text`) :
- **RAG** (ChromaDB, une collection par pharmacie) : retrouve les 3 exemples question/SQL les plus proches en sens.
- **Filtrage du schéma** (un dictionnaire Python en mémoire, recalculé au démarrage) : un score qui combine un peu de lexical et surtout de la similarité de sens, calculé par table. Garde les 15 tables les plus pertinentes sur 19 (3 toujours incluses par sécurité).

Message clé : aucun appel LLM dans le filtrage de schéma, un calcul pur, rapide, déterministe. Un schéma plus court donne un SQL de meilleure qualité sur un modèle 7b (mesuré : 13 200 caractères ramenés à 2 600, gain direct sur le taux de succès).

## 8. Génération SQL et validation structurelle (1:30)
`generate_sql()` : température 0.0 pour rester déterministe, prompt assemblé avec les rappels critiques injectés juste avant `<question>` (position de haute récence, le LLM les lit en dernier, ils l'emportent sur les vieux patterns hérités du RAG).

`validate_sql()` : pas une liste noire de mots-clés, un parseur AST (`sqlglot`) qui vérifie une seule instruction et que c'est bien un `SELECT`. À dire explicitement : *"ce n'est pas la vraie protection de sécurité, celle-ci vient de genbi_readonly et de la RLS."*

## 9. MARS-SQL, la boucle d'auto-réparation (1:30) ⭐ moment fort
C'est le point le plus démontrable techniquement. Si le SQL plante :
```
tentative 1 échoue → message d'erreur PostgreSQL exact renvoyé au LLM
                    → le LLM corrige avec le contexte de l'échec réel
                    → tentative 2 (jusqu'à 3 au total)
```
Différence avec un simple retry : le modèle voit pourquoi ça a échoué, pas juste qu'il faut réessayer. C'est une boucle de correction par feedback d'exécution, pas un nouvel essai à l'aveugle.

## 10. Validation sémantique, la cohérence plutôt que la syntaxe (1:00)
`check_result_coherence()` : le SQL s'exécute sans erreur, mais est-ce que le résultat a du sens par rapport à la question ? 3 règles (0 ligne suspecte, question scalaire avec trop de lignes, "top N" mal dimensionné). Volontairement conservateur : préfère laisser passer un cas limite plutôt que re-générer inutilement.

## 11. Humanisation et insight, le solide autour de l'incertain (1:00)
Humanisation (mois, jours, booléens) : conversions Python pures, aucune dépendance au LLM. L'insight (la phrase naturelle) est généré à température 0.1, puis post-traité par une règle qui corrige le format des montants, quoi que le LLM ait produit.

Message clé : *"Chaque étape ajoute un filet de sécurité fiable autour d'un modèle qui ne l'est pas toujours. L'architecture part du principe que le LLM va se tromper."*

## 12. Détection automatique de visualisation (0:45)
Cascade de règles par priorité (temporel donne une courbe, LIMIT donne des barres, classement donne des barres, répartition donne un camembert, sinon des barres par défaut), entièrement en Python et regex, zéro LLM. Le frontend affine encore (courbe simple ou combinée, selon le nombre de colonnes numériques).

## 13. Architecture pilotée par la configuration (1:00)
Toutes les règles métier (viz, validation sémantique, rappels de prompt) vivent dans 4 fichiers YAML, rechargeables à chaud (un point d'administration dédié) sans redémarrer Docker. Ajuster le comportement du LLM revient à éditer un fichier texte, zéro déploiement.

## 14. Discipline qualité (1:00)
Golden set de 50 questions métier (7 catégories), benchmark reproductible. Point fort à mentionner : rejet argumenté de modèles plus gros (qwen2.5-coder:14b : même score, latence deux fois plus grande, rollback documenté avec des chiffres, pas par intuition).

## 15. Sécurité, la RLS comme vraie frontière (1:00)
Récapitulatif : `genbi_readonly` (lecture seule, `NOBYPASSRLS`), plus la RLS Postgres, plus `sql_validator` (whitelist structurelle). Trois couches indépendantes. Même un LLM qui hallucine ne peut ni écrire, ni lire les données d'une autre pharmacie.

## 16. Démo live (2:00-3:00)
Poser une question réelle dans le Chat, montrer le SQL généré, le graphique, l'insight. Si le temps permet : montrer une question qui déclenche MARS-SQL (question ambiguë) pour rendre la réparation visible en direct.

## 17. Limites connues (1:00)
Honnêteté technique : Ollama est mono-thread, une seule génération à la fois, donc pas de vrai parallélisme multi-utilisateurs actuellement. Objectif assumé du projet : MVP de labo, pas mise en production. Pistes si besoin de scaler : activer le parallélisme d'Ollama, mettre en cache les questions fréquentes, passer à un serveur d'inférence avec traitement par lots.

## 18. Conclusion (0:45)
*"La BI classique gagne en fiabilité ce qu'elle perd en flexibilité. Un LLM livré tel quel fait l'inverse. Ce système essaie de ne pas choisir : la flexibilité du langage naturel, avec des garde-fous fiables à chaque étage, pour retrouver la confiance du SQL écrit à la main."*

---

## Notes de préparation
- Prévoir un filet de sécurité si Ollama est lent ou indisponible pendant la démo (capture d'écran ou vidéo courte en secours).
- Slide 9 (MARS-SQL) et 17 (limites) sont les 2 moments où l'auditoire technique pose le plus de questions. Prévoir 1 à 2 minutes de marge de chaque côté.
- Si le temps manque, les sections 7, 8 et 12 peuvent être compressées en une seule transition rapide sans perdre le fil.
