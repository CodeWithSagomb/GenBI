# Makefile pour automatiser le projet GenBI

.PHONY: help up down restart init logs ps clean dbt-init

help:
	@echo "Commandes disponibles :"
	@echo "  make up          - Démarre tous les conteneurs Docker en arrière-plan"
	@echo "  make down        - Arrête tous les conteneurs Docker"
	@echo "  make restart     - Redémarre tous les conteneurs"
	@echo "  make init        - Initialise la base de données d'Airflow et crée l'utilisateur admin"
	@echo "  make logs        - Affiche les logs en temps réel"
	@echo "  make ps          - Affiche l'état des conteneurs"
	@echo "  make clean       - Arrête les conteneurs et supprime TOUS les volumes persistants (remise à zéro)"

up:
	docker compose up -d --build

down:
	docker compose down

restart:
	docker compose restart

init:
	docker compose up -d postgres
	sleep 3
	docker compose run --rm airflow-init

logs:
	docker compose logs -f

ps:
	docker compose ps

clean:
	docker compose down -v
	rm -rf airflow/logs/*
