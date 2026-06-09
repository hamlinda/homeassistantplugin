import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .helpers import build_change_payload
from .sender import async_send_payload

_LOGGER = logging.getLogger(__name__)


class SensorReaderCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, receiver_url, interval_minutes, metadata):
        super().__init__(
            hass,
            _LOGGER,
            name="Home Assistant Sensor Reader",
            update_interval=timedelta(minutes=interval_minutes),
        )
        self.receiver_url = receiver_url
        self.metadata = metadata
        self._last_snapshot = {}

    async def async_initialize_snapshot(self):
        self._last_snapshot = await self._collect_current_snapshot()

    async def _async_update_data(self):
        current_snapshot = await self._collect_current_snapshot()
        payload = build_change_payload(current_snapshot, self._last_snapshot)
        if payload:
            try:
                await async_send_payload(self.hass, self.receiver_url, payload)
                self._last_snapshot = current_snapshot
            except Exception as err:
                raise UpdateFailed(f"Failed to send changed sensor payload: {err}")
        else:
            _LOGGER.debug("No sensor state changes detected during polling interval")
        return current_snapshot

    async def _collect_current_snapshot(self):
        snapshot = {}
        for state in self.hass.states.async_all():
            snapshot[state.entity_id] = {
                "state": state.state,
                "attributes": state.attributes,
            }
        return snapshot
