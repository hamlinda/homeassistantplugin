import asyncio
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_POLL_INTERVAL_MINUTES,
    CONF_RECEIVER_URL,
    CONF_SEND_METADATA,
    DATA_COORDINATOR,
    DEFAULT_POLL_INTERVAL_MINUTES,
    DEFAULT_RECEIVER_URL,
    MIN_POLL_INTERVAL_MINUTES,
    DOMAIN,
)
from .coordinator import SensorReaderCoordinator
from .discovery import async_discover_entities
from .helpers import load_metadata, save_metadata, validate_poll_interval, validate_receiver_url
from .sender import async_send_payload

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = entry.options or entry.data
    try:
        receiver_url = validate_receiver_url(data.get(CONF_RECEIVER_URL, DEFAULT_RECEIVER_URL))
        poll_interval = validate_poll_interval(
            data.get(CONF_POLL_INTERVAL_MINUTES, DEFAULT_POLL_INTERVAL_MINUTES)
        )
    except ValueError as err:
        _LOGGER.error("Configuration validation failed: %s", err)
        raise ConfigEntryNotReady from err

    send_metadata = data.get(CONF_SEND_METADATA, True)
    metadata = load_metadata(hass)

    if metadata is None:
        metadata = await async_discover_entities(hass)
        save_metadata(hass, metadata)
        if send_metadata and metadata:
            try:
                await async_send_payload(
                    hass,
                    receiver_url,
                    {"type": "metadata", "items": metadata},
                )
            except Exception as err:
                _LOGGER.warning(
                    "Initial metadata delivery failed; continuing startup: %s", err
                )

    coordinator = SensorReaderCoordinator(hass, receiver_url, poll_interval, metadata)
    await coordinator.async_initialize_snapshot()
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = hass.data[DOMAIN].pop(entry.entry_id, None)
    if coordinator:
        await coordinator.async_stop()
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
