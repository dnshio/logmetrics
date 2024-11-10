build:
	docker compose build

shell:
	docker compose run --build --rm app /bin/bash

ingest:
	docker compose run --build --rm app python -m bytewax.run src/logmetrics/ingest
