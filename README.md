# LogMetrics Project - Running Guide

## Using Make (Recommended)

If you have Make installed, you can use these commands:

```bash
# Build the Docker containers
make build

# Run the log ingestion pipeline
make ingest

# Start the web app (FastAPI)
make start

# Run the test suite
make test

# Clean everything up
make down
```

## Without Make

If you don't have Make installed, you can run the equivalent Docker Compose commands directly:

```bash
# Build the Docker containers
docker compose build

# Run the log ingestion pipeline
docker compose run --rm app python -m bytewax.run src/logmetrics/ingest

# Run the test suite
docker compose run --no-deps --rm app python -m pytest

# Clean up
docker compose down --remove-orphans -v
```

## Getting Started

1. Make sure you have Docker and Docker Compose installed on your system
2. Clone the repository
3. Run `make build` (or `docker compose build`)
4. Run `make ingest` (or the equivalent) to start processing logs

## Troubleshooting / common issues

You may see the following error when running `make ingest` for the first time.
This happens if the ingestion command is executed before the postgres container
has fully bootstrapped. Try the `make ingest` command again after the postgres
container has become healthy.


```bash
thread '<unnamed>' panicked at src/run.rs:126:17:
Box<dyn Any>
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/app/.venv/lib/python3.12/site-packages/bytewax/run.py", line 355, in <module>
    cli_main(**kwargs)
TypeError: (src/worker.rs:149:10) error building production dataflow
Caused by => TypeError: DBAPIError.__init__() missing 2 required positional arguments: 'params' and 'orig'
```

## Testing the API
Use the following curl command to test the API. Change `cust_22` and `from` as you wish.

```bash
curl -v -XGET -H "Content-type: application/json" 'http://0.0.0.0:8000/customers/cust_22/stats?from=2024-10-10'
```

## Implementation notes
[src/logmetrics/ingest.py](src/logmetrics/ingest.py) contains the Bytewax dataflow for processing the
[log file](data/api_requests.log), calculating stats for daily windows and then inserting those stats
into the DB. The poorly named [src/logmetrics/dataflow_helpers.py](src/logmetrics/dataflow_helpers.py)
contains all the functions and other structures used by the dataflow.

### Design notes
A key decision decision of this project was to calculate the daily stats at ingestion time and store the
stats in the DB. That decision was taken mostly to keep the scope narrow and to avoid having to calculate
stats at read time (on api response), which could be expensive. This limits future functionality such as
stats per hour or other smaller time windows.

If smaller or configurable windows were a requirement then I would consider persisting 5 min or hourly
windows at ingestion time and use bytewax to process data on the way out depending on the window size
requested. I am not sure whether that is actually a good idea or not.
