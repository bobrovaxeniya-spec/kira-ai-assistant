.PHONY: up down logs api-logs celery-logs flower

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

api-logs:
	docker-compose logs -f api

celery-logs:
	docker-compose logs -f celery_worker

flower:
	@echo "Flower UI: http://localhost:5555"
	docker-compose up flower

migrate:
	docker-compose exec api alembic upgrade head

shell:
	docker-compose exec api python
