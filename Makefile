.PHONY: up down migrate makemigration seed test logs restart ps build

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build

restart:
	docker-compose restart

ps:
	docker-compose ps

migrate:
	docker-compose exec api alembic upgrade head

makemigration:
	docker-compose exec api alembic revision --autogenerate -m "$(msg)"

seed:
	docker-compose exec api python -m app.scripts.seed_demo

test:
	docker-compose exec api pytest tests/ -v

logs:
	docker-compose logs -f api

logs-all:
	docker-compose logs -f
