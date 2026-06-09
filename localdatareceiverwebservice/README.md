# Local Data Receiver Web Service

This folder contains the local web service that receives changed sensor data from the Home Assistant plugin, stores it in a scalable local database, and exposes retrieval endpoints for history and device metadata.

## Purpose

The local data receiver is responsible for:

- accepting POST submissions from Home Assistant with changed sensor readings,
- validating payloads in JSON or CSV format,
- storing sensor history in a SQLite database optimized for queries,
- appending CSV backups for easy export,
- exposing local retrieval endpoints for history and devices,
- serving as the foundation for future complex device execution and orchestration.

## Architecture

### Core components

- `app.py` — application entrypoint and route definitions.
- `storage.py` — SQLite-backed storage manager with history and metadata support.
- `schemas.py` — payload parsing and validation logic.
- `requirements.txt` — runtime dependency declaration.

### Design principles

- `localhost` first: the service binds to `127.0.0.1` by default for local-only operation.
- `SQLite` persistence: optimized storage with indexes for fast history queries and long-term growth.
- `JSON + CSV` compatibility: accepts structured JSON payloads and CSV uploads from the plugin.
- `transactional writes`: storage writes are grouped and committed atomically.
- `scalability`: the database schema is designed to support future extended fields and command execution.

## Folder structure

- `app.py` — web server and route handling for `/sensor-updates`, `/history`, `/devices`, `/execute`, and `/status`.
- `storage.py` — low-level database schema management and persistence operations.
- `schemas.py` — schema enforcement and normalization for incoming payloads.
- `requirements.txt` — includes `aiohttp`.
- `README.md` — this file.

## Dependencies

The service currently depends on:

- `aiohttp>=3.8.0`

It otherwise uses Python standard libraries for `json`, `sqlite3`, `logging`, and `pathlib`.

## Configuration

The service supports optional environment variables:

- `LOCAL_RECEIVER_HOST` — host interface. Default: `127.0.0.1`
- `LOCAL_RECEIVER_PORT` — port number. Default: `8000`
- `LOCAL_RECEIVER_DATA_DIR` — directory for SQLite and CSV storage. Default: `data`

## Storage model

### SQLite tables

- `device_metadata`
  - stores the discovered entity metadata from Home Assistant.
  - fields include `entity_id`, `device_id`, `friendly_name`, `domain`, `unit_of_measurement`, `writeable`, `supported_services`, and `state_attributes`.

- `sensor_history`
  - records every changed sensor value received.
  - fields include `timestamp`, `device_id`, `entity_id`, `friendly_name`, `domain`, `old_state`, `new_state`, `unit_of_measurement`, `attributes`, and `payload_type`.

- indexes on `entity_id` and `timestamp` accelerate history queries.

### CSV backup

The service also appends each received change record to `data/sensor_changes.csv` for quick export and offline analysis.

## API endpoints

### `POST /sensor-updates`

Receives changed sensor payloads.

Supported payload formats:

- JSON with keys:
  - `type`: `sensor_changes` or `metadata`
  - `items`: list of records
- CSV with headers (when content-type is `text/csv` or the payload appears to be CSV)

The service validates the payload and stores metadata or history records accordingly.

### `GET /history`

Query stored history.

Optional query parameters:

- `entity_id`
- `start` — ISO timestamp lower bound
- `end` — ISO timestamp upper bound
- `limit` — maximum number of records to return

### `GET /devices`

Returns all persisted device metadata records.

### `POST /execute`

Placeholder for future device execution and complex control operations.

### `GET /status`

Returns service health and available endpoints.

## Comments and code information

The code includes scoped comments for:

- lifecycle and initialization in `app.py`,
- payload validation and CSV normalization in `schemas.py`,
- transactional storage operations and schema definitions in `storage.py`.

The comments are intentionally scaled to explain high-level intent without overwhelming implementation details.

## Future optimization and scaling

### Storage scaling

- SQLite is sufficient for local data retention and supports indexing for efficient searches.
- The schema separates metadata from history so device catalogs can be cached and reused.
- The service writes history using a single transaction per payload for durability.
- Future expansion can add retention pruning, partitioned history tables, or a richer analytics layer.

### Application expansion

- Add `/execute` behavior to perform device actions or schedule combinations.
- Add retention, cleanup, and rollup endpoints.
- Add UI or API layers for query-based analytics and rule configuration.

## Running the service

Install dependencies:

```bash
pip install -r localdatareceiverwebservice/requirements.txt
```

Start the service:

```bash
python -m localdatareceiverwebservice.app
```

By default, it listens on `http://127.0.0.1:8000` and stores data under `localdatareceiverwebservice/data/`.

## Notes

This service is designed to be local, lightweight, and extensible. It provides a stable ingestion endpoint for the Home Assistant plugin and a durable storage foundation for future data evaluation and device control workflows.
