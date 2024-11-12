build:
	docker compose build

shell:
	docker compose run --rm app /bin/bash

ingest:
	docker compose run --rm app python -m bytewax.run src/logmetrics/ingest

test:
	docker compose run --no-deps --rm app python -m pytest

format:
	docker compose run --rm app black /app

lint:
	docker compose run --no-deps --rm app ruff check
