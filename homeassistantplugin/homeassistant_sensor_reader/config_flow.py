import logging
from urllib.parse import urlparse
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.helpers import config_validation as cv
from .const import (
    DOMAIN,
    CONF_RECEIVER_URL,
    CONF_POLL_INTERVAL_MINUTES,
    CONF_SEND_METADATA,
    DEFAULT_POLL_INTERVAL_MINUTES,
    DEFAULT_RECEIVER_URL,
    MIN_POLL_INTERVAL_MINUTES,
)
from .helpers import validate_receiver_url, validate_poll_interval

_LOGGER = logging.getLogger(__name__)


class HomeAssistantSensorReaderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            CONF_RECEIVER_URL,
                            default=DEFAULT_RECEIVER_URL,
                        ): cv.string,
                        vol.Optional(
                            CONF_POLL_INTERVAL_MINUTES,
                            default=DEFAULT_POLL_INTERVAL_MINUTES,
                        ): vol.All(vol.Coerce(int), vol.Range(min=MIN_POLL_INTERVAL_MINUTES)),
                        vol.Optional(CONF_SEND_METADATA, default=True): cv.boolean,
                    }
                ),
            )

        errors = {}
        try:
            receiver_url = validate_receiver_url(user_input[CONF_RECEIVER_URL])
            poll_interval = validate_poll_interval(user_input[CONF_POLL_INTERVAL_MINUTES])
        except ValueError as err:
            _LOGGER.warning("Invalid configuration input: %s", err)
            errors["base"] = str(err)
        else:
            return self.async_create_entry(
                title="Home Assistant Sensor Reader",
                data={
                    CONF_RECEIVER_URL: receiver_url,
                    CONF_POLL_INTERVAL_MINUTES: poll_interval,
                    CONF_SEND_METADATA: user_input.get(CONF_SEND_METADATA, True),
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_RECEIVER_URL,
                        default=user_input.get(CONF_RECEIVER_URL, DEFAULT_RECEIVER_URL),
                    ): cv.string,
                    vol.Optional(
                        CONF_POLL_INTERVAL_MINUTES,
                        default=user_input.get(
                            CONF_POLL_INTERVAL_MINUTES,
                            DEFAULT_POLL_INTERVAL_MINUTES,
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=MIN_POLL_INTERVAL_MINUTES)),
                    vol.Optional(CONF_SEND_METADATA, default=user_input.get(CONF_SEND_METADATA, True)): cv.boolean,
                }
            ),
            errors=errors,
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Options", data=user_input)

        current = self.config_entry.options or self.config_entry.data
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_RECEIVER_URL,
                        default=current.get(CONF_RECEIVER_URL, DEFAULT_RECEIVER_URL),
                    ): cv.string,
                    vol.Optional(
                        CONF_POLL_INTERVAL_MINUTES,
                        default=current.get(
                            CONF_POLL_INTERVAL_MINUTES,
                            DEFAULT_POLL_INTERVAL_MINUTES,
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=MIN_POLL_INTERVAL_MINUTES)),
                    vol.Optional(
                        CONF_SEND_METADATA,
                        default=current.get(CONF_SEND_METADATA, True),
                    ): cv.boolean,
                }
            ),
        )


def async_get_options_flow(config_entry):
    return OptionsFlowHandler(config_entry)
