# Makefile pour automatiser le projet GenBI

.PHONY: help dev up down restart init logs ps clean dbt-test

help:
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════╗"
	@echo "║              GenBI — Commandes disponibles               ║"
	@echo "╠══════════════════════════════════════════════════════════╣"
	@echo "║  DEV (léger — pour le développement quotidien)           ║"
	@echo "║  make dev       Démarre postgres + backend + frontend     ║"
	@echo "║                 (~135 MB RAM, machine froide)             ║"
	@echo "╠══════════════════════════════════════════════════════════╣"
	@echo "║  FULL (lourd — Airflow + Metabase inclus)                ║"
	@echo "║  make up        Démarre TOUS les services                 ║"
	@echo "║  make init      Initialise Airflow (1ère fois)            ║"
	@echo "╠══════════════════════════════════════════════════════════╣"
	@echo "║  UTILITAIRES                                              ║"
	@echo "║  make down      Arrête tous les conteneurs                ║"
	@echo "║  make ps        État des conteneurs                       ║"
	@echo "║  make logs      Logs en temps réel                        ║"
	@echo "║  make dbt-test  Lance les tests dbt (149 tests)           ║"
	@echo "║  make clean     Reset complet (supprime les volumes)      ║"
	@echo "╚══════════════════════════════════════════════════════════╝"
	@echo ""

# Mode développement — léger : postgres + backend + frontend uniquement
dev:
	docker compose up -d
	@echo ""
	@echo "✓ Mode DEV démarré (postgres + backend + frontend)"
	@echo "  Backend  → http://localhost:8000/docs"
	@echo "  Frontend → http://localhost:5173"
	@echo ""

# Mode complet — tous les services (Airflow + Metabase inclus)
up:
	docker compose --profile full up -d --build
	@echo ""
	@echo "✓ Mode FULL démarré (tous les services)"
	@echo "  Backend  → http://localhost:8000/docs"
	@echo "  Frontend → http://localhost:5173"
	@echo "  Airflow  → http://localhost:8080"
	@echo "  Metabase → http://localhost:3000"
	@echo ""

down:
	docker compose --profile full down

restart:
	docker compose --profile full restart

# Initialise Airflow (à lancer une seule fois après make up)
init:
	docker compose --profile full up -d postgres
	sleep 3
	docker compose --profile full run --rm airflow-init

logs:
	docker compose --profile full logs -f

ps:
	docker compose --profile full ps

# Lance les tests dbt (depuis dbt_project/)
dbt-test:
	cd dbt_project && dbt test --no-partial-parse

# Reset complet — supprime TOUS les volumes (irréversible)
clean:
	docker compose --profile full down -v
	rm -rf airflow/logs/*
