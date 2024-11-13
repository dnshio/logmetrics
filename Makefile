build:
	docker compose build

shell:
	docker compose run --rm app /bin/bash

start: build
	docker compose up

ingest:
	docker compose run --rm app python -m bytewax.run src/logmetrics/ingest

test:
	docker compose run --no-deps --rm app python -m pytest

format:
	docker compose run --rm app black /app

lint:
	docker compose run --no-deps --rm app ruff check

# Clean everything
down:
	docker compose down --remove-orphans -v
