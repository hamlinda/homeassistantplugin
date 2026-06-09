import asyncio
import json
import logging
import os
from aiohttp import web
from pathlib import Path
from .schemas import validate_payload, parse_csv_payload
from .storage import LocalDataStore

_LOGGER = logging.getLogger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_DATA_DIR = "data"
DEFAULT_DB_NAME = "sensor_receiver.db"
DEFAULT_CSV_NAME = "sensor_changes.csv"


def create_app(data_path: Path) -> web.Application:
    """Create and configure the local data receiver application."""
    app = web.Application()

    data_path.mkdir(parents=True, exist_ok=True)
    db_path = data_path / DEFAULT_DB_NAME
    csv_path = data_path / DEFAULT_CSV_NAME

    datastore = LocalDataStore(db_path, csv_path)
    app["datastore"] = datastore

    app.router.add_post("/sensor-updates", handle_sensor_updates)
    app.router.add_get("/history", handle_get_history)
    app.router.add_get("/devices", handle_get_devices)
    app.router.add_post("/execute", handle_execute)
    app.router.add_get("/status", handle_status)

    return app


async def handle_sensor_updates(request: web.Request) -> web.Response:
    """Receive changed sensor readings and store them safely."""
    datastore: LocalDataStore = request.app["datastore"]
    content_type = request.content_type or ""
    raw_body = await request.read()

    try:
        if content_type == "text/csv" or raw_body.lstrip().startswith(b"entity_id"):
            payload = parse_csv_payload(raw_body.decode("utf-8"))
        else:
            payload = await request.json()
    except json.JSONDecodeError as err:
        _LOGGER.warning("Invalid JSON payload: %s", err)
        return web.json_response({"error": "Invalid JSON payload"}, status=400)
    except ValueError as err:
        _LOGGER.warning("Invalid sensor update payload: %s", err)
        return web.json_response({"error": str(err)}, status=400)

    normalized_payload = validate_payload(payload)
    metadata_items = normalized_payload.get("metadata_items")
    change_items = normalized_payload.get("change_items")

    if metadata_items:
        datastore.save_metadata_items(metadata_items)
        _LOGGER.info("Saved %s metadata items", len(metadata_items))

    if change_items:
        datastore.save_sensor_changes(change_items)
        datastore.append_csv(change_items)
        _LOGGER.info("Stored %s changed sensor records", len(change_items))

    return web.json_response(
        {
            "status": "accepted",
            "metadata_items": len(metadata_items) if metadata_items else 0,
            "change_items": len(change_items) if change_items else 0,
        }
    )


async def handle_get_history(request: web.Request) -> web.Response:
    """Return stored history records with optional filtering."""
    datastore: LocalDataStore = request.app["datastore"]
    entity_id = request.query.get("entity_id")
    limit = int(request.query.get("limit", "100"))
    start = request.query.get("start")
    end = request.query.get("end")

    records = datastore.query_history(entity_id=entity_id, start=start, end=end, limit=limit)
    return web.json_response({"history": records})


async def handle_get_devices(request: web.Request) -> web.Response:
    """Return the current device metadata catalog."""
    datastore: LocalDataStore = request.app["datastore"]
    devices = datastore.query_devices()
    return web.json_response({"devices": devices})


async def handle_execute(request: web.Request) -> web.Response:
    """Placeholder endpoint for executing device commands in the future."""
    return web.json_response(
        {"status": "not_implemented", "message": "Device execution is planned for future versions."},
        status=501,
    )


async def handle_status(request: web.Request) -> web.Response:
    """Return operational status and endpoint health."""
    return web.json_response(
        {
            "status": "ok",
            "endpoints": ["/sensor-updates", "/history", "/devices", "/execute", "/status"],
        }
    )


def main() -> None:
    """Start the local receiver web service bound to localhost."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    host = os.getenv("LOCAL_RECEIVER_HOST", DEFAULT_HOST)
    port = int(os.getenv("LOCAL_RECEIVER_PORT", DEFAULT_PORT))
    data_dir = Path(os.getenv("LOCAL_RECEIVER_DATA_DIR", DEFAULT_DATA_DIR))

    app = create_app(data_dir)
    web.run_app(app, host=host, port=port)


if __name__ == "__main__":
    main()
