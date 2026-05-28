# Feature Specification : Interface de Chat GenBI

**Feature** : `003-frontend-chat`
**Créée** : 2026-05-28
**Statut** : Draft
**Dépend de** : `002-backend-api` (endpoints /chat et /execute opérationnels)

---

## Contexte Métier

Le pharmacien dispose d'une interface web pour discuter avec ses données comme avec un assistant. Il tape sa question, voit le raisonnement de l'IA (le SQL généré), et visualise les résultats sous forme de tableau ou de graphique adapté.

---

## User Stories & Scénarios de Test

### User Story 1 — Le pharmacien pose une question et voit les résultats (Priorité : P1)

L'utilisateur tape une question dans un champ de saisie, appuie sur Entrée, et voit apparaître progressivement : la question, l'indication "analyse en cours...", le SQL généré, puis le tableau de résultats.

**Pourquoi P1** : C'est le flux principal. Tout le reste est amélioration.

**Test indépendant** : Ouvrir l'interface sur localhost:5173, taper une question, vérifier que le tableau de résultats s'affiche.

**Scénarios d'acceptance** :
1. **Étant donné** l'interface ouverte, **Quand** l'utilisateur tape "CA de Mars 2026" et appuie sur Entrée, **Alors** un tableau avec les résultats apparaît en moins de 30 secondes.
2. **Étant donné** une erreur du backend, **Quand** la réponse est une erreur, **Alors** un message d'erreur clair en français apparaît — pas de page blanche.
3. **Étant donné** une réponse avec un seul chiffre, **Quand** affichée, **Alors** le montant est formaté avec séparateur de milliers et "FCFA" en suffixe.

---

### User Story 2 — Les résultats sont visualisés en graphiques (Priorité : P2)

Quand les résultats sont adaptés (séries temporelles, comparaisons), l'interface propose automatiquement un graphique interactif en plus du tableau.

**Scénarios d'acceptance** :
1. **Étant donné** des résultats avec une colonne date et une colonne montant, **Quand** affichés, **Alors** un graphique en courbe est proposé automatiquement.
2. **Étant donné** des résultats avec des catégories (top produits), **Quand** affichés, **Alors** un graphique en barres est proposé.
3. **Étant donné** un résultat qui est un seul chiffre, **Quand** affiché, **Alors** aucun graphique n'est proposé — juste la valeur mise en avant.

---

### User Story 3 — L'utilisateur peut corriger une réponse incorrecte (Priorité : P3)

Si le SQL généré est incorrect, l'utilisateur peut l'éditer directement dans l'interface et ré-exécuter la version corrigée.

**Scénarios d'acceptance** :
1. **Étant donné** un SQL affiché, **Quand** l'utilisateur clique sur "Modifier le SQL", **Alors** un éditeur de texte s'ouvre avec le SQL actuel.
2. **Étant donné** un SQL modifié, **Quand** l'utilisateur clique sur "Ré-exécuter", **Alors** les nouveaux résultats remplacent les anciens.

---

## Critères de Succès Mesurables

- **CS-001** : Un pharmacien sans formation technique peut poser une question et lire les résultats sans aide en moins de 5 minutes de prise en main.
- **CS-002** : L'interface affiche les résultats en moins de 30 secondes après soumission de la question.
- **CS-003** : L'interface fonctionne sur les navigateurs modernes (Chrome, Firefox, Safari) sans erreur.
- **CS-004** : L'interface reste utilisable sur un écran 13 pouces (résolution 1280×800 minimum).

---

## Hypothèses

- Le backend est opérationnel sur `http://localhost:8000`.
- La variable d'environnement `VITE_API_URL` est correctement configurée.
- Le design system CSS existant (`index.css`) est réutilisé — pas de refonte graphique.
- Les graphiques utilisent Recharts (déjà dans les dépendances npm).
