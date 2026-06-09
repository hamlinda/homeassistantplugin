import asyncio
import logging
from aiohttp import ClientError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)


async def async_send_payload(hass, receiver_url, payload, attempts=3):
    session = async_get_clientsession(hass)
    for attempt in range(1, attempts + 1):
        try:
            _LOGGER.debug("Sending payload to %s (attempt %s)", receiver_url, attempt)
            async with session.post(receiver_url, json=payload, timeout=30) as response:
                response_text = await response.text()
                if response.status >= 400:
                    raise ClientError(
                        f"Receiver returned {response.status}: {response_text}"
                    )
                _LOGGER.info(
                    "Successfully delivered payload to %s with %s items",
                    receiver_url,
                    len(payload.get("items", [])),
                )
                return
        except (ClientError, asyncio.TimeoutError) as err:
            _LOGGER.warning(
                "Failed to send payload to %s on attempt %s: %s",
                receiver_url,
                attempt,
                err,
            )
            if attempt == attempts:
                _LOGGER.error("Giving up after %s failed delivery attempts", attempts)
                raise
            await asyncio.sleep(attempt * 2)
