import csv
import json
from io import StringIO
from typing import Any, Dict, List


def _ensure_string(value: Any) -> str:
    return "" if value is None else str(value)


def parse_csv_payload(csv_text: str) -> Dict[str, Any]:
    """Parse a CSV payload into the normalized internal payload structure."""
    reader = csv.DictReader(StringIO(csv_text))
    if not reader.fieldnames:
        raise ValueError("CSV payload must include headers")

    items = []
    for row in reader:
        attributes = row.get("attributes", "")
        if attributes:
            try:
                attributes = json.loads(attributes)
            except json.JSONDecodeError:
                attributes = {"raw": attributes}
        else:
            attributes = {}

        items.append(
            {
                "entity_id": _ensure_string(row.get("entity_id")),
                "device_id": _ensure_string(row.get("device_id")),
                "friendly_name": _ensure_string(row.get("friendly_name")),
                "domain": _ensure_string(row.get("domain")),
                "old_state": _ensure_string(row.get("old_state")),
                "new_state": _ensure_string(row.get("new_state")),
                "unit_of_measurement": _ensure_string(row.get("unit_of_measurement")),
                "attributes": attributes,
                "timestamp": _ensure_string(row.get("timestamp")),
                "payload_type": _ensure_string(row.get("payload_type", "sensor_changes")),
            }
        )

    return {"type": "sensor_changes", "items": items}


def validate_payload(payload: Any) -> Dict[str, Any]:
    """Validate incoming payloads and normalize metadata or change records."""
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a JSON object")

    payload_type = payload.get("type")
    if payload_type == "metadata":
        items = payload.get("items")
        if not isinstance(items, list):
            raise ValueError("Metadata payload items must be a list")
        for item in items:
            _validate_metadata_item(item)
        return {"metadata_items": items, "change_items": []}

    if payload_type == "sensor_changes":
        items = payload.get("items")
        if not isinstance(items, list):
            raise ValueError("Sensor changes payload items must be a list")
        validated_items = [_validate_change_item(item) for item in items]
        return {"metadata_items": [], "change_items": validated_items}

    raise ValueError("Payload type must be 'metadata' or 'sensor_changes'")


def _validate_metadata_item(item: Any) -> None:
    if not isinstance(item, dict):
        raise ValueError("Each metadata item must be an object")
    required_keys = {"entity_id", "domain", "friendly_name"}
    if not required_keys.issubset(item):
        missing = required_keys - set(item)
        raise ValueError(f"Metadata item missing keys: {missing}")


def _validate_change_item(item: Any) -> Dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError("Each sensor change item must be an object")
    if "entity_id" not in item or "new_state" not in item:
        raise ValueError("Sensor change items must include entity_id and new_state")

    attributes = item.get("attributes")
    if attributes is None:
        attributes = {}
    elif not isinstance(attributes, dict):
        raise ValueError("Sensor change item attributes must be an object")

    return {
        "entity_id": _ensure_string(item.get("entity_id")),
        "device_id": _ensure_string(item.get("device_id")),
        "friendly_name": _ensure_string(item.get("friendly_name")),
        "domain": _ensure_string(item.get("domain")),
        "old_state": _ensure_string(item.get("old_state")),
        "new_state": _ensure_string(item.get("new_state")),
        "unit_of_measurement": _ensure_string(item.get("unit_of_measurement")),
        "attributes": attributes,
        "timestamp": _ensure_string(item.get("timestamp")),
        "payload_type": _ensure_string(item.get("payload_type", "sensor_changes")),
    }
