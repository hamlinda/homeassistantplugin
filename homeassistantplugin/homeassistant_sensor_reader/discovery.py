import logging
from homeassistant.helpers import entity_registry as er
from .helpers import build_metadata_record

_LOGGER = logging.getLogger(__name__)


async def async_discover_entities(hass):
    registry = er.async_get(hass)
    states = hass.states.async_all()
    metadata = []

    for state in states:
        entity_entry = registry.async_get(state.entity_id)
        try:
            metadata.append(build_metadata_record(state, entity_entry))
        except Exception as err:
            _LOGGER.warning("Skipping entity %s during discovery: %s", state.entity_id, err)

    _LOGGER.debug("Discovered %s entities during initial metadata generation", len(metadata))
    return metadata
