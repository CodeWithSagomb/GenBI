# GenBI — Makefile
# Toutes les commandes du projet en un seul endroit.
# Lancer depuis la racine du projet : /Desktop/GenerativeBI/GenBI/

.PHONY: help \
        dev up down restart ps logs clean \
        seed dbt-run dbt-parse dbt-test \
        test test-backend test-frontend benchmark \
        health shell db-shell \
        branch status

DBT_DIR      = dbt_project
DBT_PROFILES = ~/.dbt
PYTHON       = /opt/homebrew/bin/python3.11
BACKEND      = genbi_backend
FRONTEND     = genbi_frontend

# ─── AIDE ────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════╗"
	@echo "║                GenBI — Commandes disponibles                 ║"
	@echo "╠══════════════════════════════════════════════════════════════╣"
	@echo "║  SYSTÈME                                                      ║"
	@echo "║  make dev          Démarre postgres + backend + frontend      ║"
	@echo "║  make up           Démarre TOUS les services (Airflow+Meta)   ║"
	@echo "║  make down         Arrête tous les conteneurs                 ║"
	@echo "║  make restart      Redémarre tous les conteneurs              ║"
	@echo "║  make ps           État des conteneurs                        ║"
	@echo "║  make logs         Logs en temps réel                         ║"
	@echo "║  make health       Vérifie que tous les services répondent    ║"
	@echo "║  make clean        Reset complet — supprime les volumes ⚠️    ║"
	@echo "╠══════════════════════════════════════════════════════════════╣"
	@echo "║  DONNÉES                                                      ║"
	@echo "║  make seed         Génère les données simulées (seed_data.py) ║"
	@echo "║  make dbt-run      Exécute les modèles dbt (staging + marts)  ║"
	@echo "║  make dbt-parse    Régénère le manifest.json (requis au boot) ║"
	@echo "║  make dbt-test     Lance les 149 tests dbt                    ║"
	@echo "╠══════════════════════════════════════════════════════════════╣"
	@echo "║  TESTS                                                        ║"
	@echo "║  make test         Lance tous les tests (backend + frontend)  ║"
	@echo "║  make test-backend Lance pytest backend (122 tests)           ║"
	@echo "║  make test-frontend Lance Vitest frontend (44 tests)          ║"
	@echo "║  make benchmark    Lance le benchmark LLM (30 questions)      ║"
	@echo "╠══════════════════════════════════════════════════════════════╣"
	@echo "║  ACCÈS RAPIDE                                                 ║"
	@echo "║  make shell        Shell dans le conteneur backend            ║"
	@echo "║  make db-shell     Shell PostgreSQL                           ║"
	@echo "╠══════════════════════════════════════════════════════════════╣"
	@echo "║  GIT                                                          ║"
	@echo "║  make branch name=feat/ma-feature  Crée une branche          ║"
	@echo "║  make status       État git du projet                         ║"
	@echo "╚══════════════════════════════════════════════════════════════╝"
	@echo ""

# ─── SYSTÈME ─────────────────────────────────────────────────────────────────
dev:
	docker compose up -d
	@echo ""
	@echo "✅ Système démarré"
	@echo "   Frontend  → http://localhost:5173"
	@echo "   Backend   → http://localhost:8000/docs"
	@echo "   Postgres  → localhost:5432"
	@echo ""

up:
	docker compose --profile full up -d --build
	@echo ""
	@echo "✅ Mode FULL démarré"
	@echo "   Frontend  → http://localhost:5173"
	@echo "   Backend   → http://localhost:8000/docs"
	@echo "   Airflow   → http://localhost:8080"
	@echo "   Metabase  → http://localhost:3000"
	@echo ""

down:
	docker compose --profile full down

restart:
	docker compose restart genbi-backend genbi-frontend

ps:
	docker compose --profile full ps

logs:
	docker compose logs -f --tail=50

health:
	@echo "🔍 Vérification des services..."
	@curl -s http://localhost:8000/ | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ Backend  :', d['status'])" 2>/dev/null || echo "❌ Backend  : non joignable"
	@curl -s http://localhost:5173 > /dev/null 2>&1 && echo "✅ Frontend : en ligne" || echo "❌ Frontend : non joignable"
	@docker exec genbi_postgres pg_isready -U postgres > /dev/null 2>&1 && echo "✅ Postgres : healthy" || echo "❌ Postgres : non joignable"
	@curl -s http://localhost:11434/api/tags > /dev/null 2>&1 && echo "✅ Ollama   : en ligne" || echo "❌ Ollama   : non joignable"
	@echo ""

clean:
	@echo "⚠️  Suppression de TOUS les volumes (irréversible dans 5s...)"
	@sleep 5
	docker compose --profile full down -v
	rm -rf airflow/logs/*

# ─── DONNÉES ─────────────────────────────────────────────────────────────────
seed:
	@echo "🌱 Génération des données simulées..."
	$(PYTHON) seed_data.py
	@echo "✅ Données seedées"

dbt-run:
	@echo "⚙️  Exécution des modèles dbt..."
	cd $(DBT_DIR) && dbt run --profiles-dir $(DBT_PROFILES) --project-dir .
	@echo "✅ Modèles dbt exécutés"

dbt-parse:
	@echo "📄 Régénération du manifest.json..."
	cd $(DBT_DIR) && dbt parse --profiles-dir $(DBT_PROFILES) --project-dir .
	docker restart genbi_backend
	@echo "✅ Manifest régénéré — backend redémarré"

dbt-test:
	@echo "🧪 Tests dbt..."
	cd $(DBT_DIR) && dbt test --profiles-dir $(DBT_PROFILES) --project-dir . --no-partial-parse

# ─── TESTS ───────────────────────────────────────────────────────────────────
test: test-backend test-frontend
	@echo ""
	@echo "✅ Tous les tests terminés"

test-backend:
	@echo "🧪 Tests backend (pytest)..."
	docker exec genbi_backend python -m pytest tests/ -v --tb=short -q

test-frontend:
	@echo "🧪 Tests frontend (Vitest)..."
	docker exec genbi_frontend npm run test -- --run

benchmark:
	@echo "📊 Benchmark LLM (30 questions golden)..."
	docker exec genbi_backend python -m pytest tests/benchmark/ -v --tb=short

# ─── ACCÈS RAPIDE ────────────────────────────────────────────────────────────
shell:
	docker exec -it genbi_backend /bin/bash

db-shell:
	docker exec -it genbi_postgres psql -U postgres -d genbi

# ─── GIT ─────────────────────────────────────────────────────────────────────
branch:
	@if [ -z "$(name)" ]; then echo "❌ Usage: make branch name=feat/ma-feature"; exit 1; fi
	git checkout develop && git pull origin develop
	git checkout -b $(name)
	@echo "✅ Branche $(name) créée depuis develop"

status:
	@echo "📋 État git :"
	@git branch -a
	@echo ""
	@git log --oneline -5
	@echo ""
	@git status -s
