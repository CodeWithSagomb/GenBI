# Feature Specification : RAG & Boucle de Feedback

**Feature** : `004-rag-feedback`
**Créée** : 2026-05-28
**Statut** : Backlog (Phase 5 — future)
**Dépend de** : `003-frontend-chat` (interface de validation requise)

---

## Contexte Métier

Au fil de l'utilisation, les questions récurrentes des pharmaciens et les SQL validés comme corrects sont mémorisés. L'IA les utilise comme exemples (few-shot) pour améliorer la précision des prochaines réponses sans ré-entraînement.

---

## User Stories

### User Story 1 — L'utilisateur valide une bonne réponse (Priorité : P1)

Après avoir reçu un résultat correct, l'utilisateur clique "✅ Correct" — la paire question/SQL est automatiquement enregistrée comme exemple de référence.

### User Story 2 — L'IA utilise les exemples passés pour répondre mieux (Priorité : P1)

Lors d'une nouvelle question similaire à une déjà validée, l'IA reçoit automatiquement l'exemple comme contexte supplémentaire et produit un SQL plus précis.

### User Story 3 — L'utilisateur corrige et enregistre un SQL défaillant (Priorité : P2)

L'utilisateur corrige un SQL incorrect dans l'interface, valide la correction, et cet exemple corrigé est ajouté à la base de référence.

---

## Critères de Succès Mesurables

- **CS-001** : Après 20 exemples validés, la précision des réponses similaires augmente d'au moins 15% mesurable par comparaison avant/après.
- **CS-002** : L'enregistrement d'un exemple validé prend moins de 2 secondes.
- **CS-003** : La base vectorielle locale (ChromaDB) est requêtable hors-ligne.

---

## Hypothèses

- ChromaDB est déjà dans les dépendances backend (`requirements.txt`).
- Le modèle d'embedding est disponible via Ollama (`nomic-embed-text`).
- Les exemples sont stockés localement — jamais envoyés à un service externe.
