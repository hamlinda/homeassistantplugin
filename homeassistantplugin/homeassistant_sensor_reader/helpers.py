import json
import logging
import os
import ipaddress
from urllib.parse import urlparse
from homeassistant.const import CONF_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from .const import DEFAULT_RECEIVER_URL, MIN_POLL_INTERVAL_MINUTES, METADATA_FILE

_LOGGER = logging.getLogger(__name__)

WRITEABLE_DOMAINS = {
    "switch",
    "light",
    "climate",
    "cover",
    "lock",
    "fan",
    "input_boolean",
    "input_number",
    "input_select",
    "scene",
    "script",
    "media_player",
}


def validate_receiver_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Receiver URL must use http or https")
    if not parsed.hostname:
        raise ValueError("Receiver URL must include a hostname")
    if not is_local_address(parsed.hostname):
        raise ValueError("Receiver URL must target localhost or a private address")
    return url


def validate_poll_interval(value: int) -> int:
    try:
        interval = int(value)
    except (TypeError, ValueError):
        raise ValueError("Polling interval must be an integer")
    if interval < MIN_POLL_INTERVAL_MINUTES:
        _LOGGER.warning(
            "Polling interval %s is below minimum, defaulting to %s minutes",
            interval,
            MIN_POLL_INTERVAL_MINUTES,
        )
        return MIN_POLL_INTERVAL_MINUTES
    return interval


def is_local_address(hostname: str) -> bool:
    if hostname in {"localhost", "127.0.0.1", "::1"}:
        return True
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return False
    return address.is_private


def load_metadata(hass: HomeAssistant):
    file_path = hass.config.path(METADATA_FILE)
    if not os.path.isfile(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError) as err:
        _LOGGER.warning("Unable to read saved metadata: %s", err)
        return None


def save_metadata(hass: HomeAssistant, metadata):
    file_path = hass.config.path(METADATA_FILE)
    try:
        with open(file_path, "w", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2)
    except OSError as err:
        _LOGGER.error("Unable to save metadata file: %s", err)


def build_metadata_record(state, entity_entry=None):
    attributes = state.attributes or {}
    domain = state.entity_id.split(".", 1)[0]
    unit = attributes.get(CONF_UNIT_OF_MEASUREMENT)
    has_writeable = domain in WRITEABLE_DOMAINS
    supported_services = []
    if has_writeable:
        supported_services.append(f"{domain}.turn_on")
        supported_services.append(f"{domain}.turn_off")
    return {
        "device_id": getattr(entity_entry, "device_id", None) if entity_entry else None,
        "entity_id": state.entity_id,
        "friendly_name": attributes.get("friendly_name", state.name),
        "domain": domain,
        "current_value": state.state,
        "unit_of_measurement": unit,
        "data_type": type(state.state).__name__,
        "writeable": has_writeable,
        "supported_services": supported_services,
        "state_attributes": {k: v for k, v in attributes.items() if k not in {"friendly_name"}},
    }


def build_change_payload(current_snapshot, previous_snapshot):
    changed = []
    for entity_id, current in current_snapshot.items():
        previous = previous_snapshot.get(entity_id)
        if previous is None or current["state"] != previous["state"] or current["attributes"] != previous["attributes"]:
            changed.append(
                {
                    "entity_id": entity_id,
                    "domain": entity_id.split(".", 1)[0],
                    "new_state": current["state"],
                    "old_state": previous["state"] if previous else None,
                    "attributes": current["attributes"],
                }
            )
    return {"type": "sensor_changes", "items": changed} if changed else None
