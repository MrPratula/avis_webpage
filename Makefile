
COMPOSE_CMD=docker-compose
SERVICE_NAME=mr_avis_website

build:
	$(COMPOSE_CMD) build

up:
	$(COMPOSE_CMD) up -d

down:
	$(COMPOSE_CMD) down

restart: down build up

logs:
	$(COMPOSE_CMD) logs -f $(SERVICE_NAME)

status:
	$(COMPOSE_CMD) ps