# Home Assistant Sensor Reader Plugin

This directory contains the Home Assistant integration for the `homeassistant_sensor_reader` plugin. It is designed to:

- discover all registered sensors, entities, devices, and runtime-modifiable values on first launch,
- generate a metadata table of devices and readings,
- poll for changes at a user-configurable interval,
- send only changed sensor data to a locally addressable endpoint,
- enforce a default minimum polling interval of 5 minutes.

## Plugin structure

The plugin is located in `homeassistantplugin/homeassistant_sensor_reader/` and includes:

- `manifest.json` — Home Assistant integration manifest.
- `__init__.py` — integration setup, config entry handling, metadata discovery, and coordinator startup.
- `const.py` — constants and configuration defaults.
- `helpers.py` — utility functions for validation, metadata build, and snapshot diff generation.
- `discovery.py` — first-launch discovery logic using entity and state registries.
- `sender.py` — HTTP payload delivery and retry/error handling.
- `coordinator.py` — the update coordinator responsible for polling and change detection.
- `config_flow.py` — configuration flow entry and options flow for Home Assistant UI.

## Installation

To install this plugin into Home Assistant, copy the `homeassistant_sensor_reader` folder into your Home Assistant `custom_components` directory.

Example:

1. Create or open `config/custom_components/` in your Home Assistant installation.
2. Copy the folder:
   - `homeassistantplugin/homeassistant_sensor_reader` -> `config/custom_components/homeassistant_sensor_reader`
3. Restart Home Assistant.
4. Add the integration through the UI configuration flow.

## Dependencies

This integration uses Home Assistant core APIs and the built-in `aiohttp` HTTP client session provided by Home Assistant.

### Required platform support

- Home Assistant core
- Local polling integration style
- Entity registry and state registry access

There are no external Python package dependencies beyond those already provided by Home Assistant.

## Configuration

The integration supports the following configurable settings during setup:

- `receiver_url` — local endpoint URL to send changed sensor data. Default: `http://localhost:8000/sensor-updates`
- `poll_interval_minutes` — polling interval in minutes. Default: `5`. Minimum enforced: `5`.
- `send_metadata` — whether to send initial discovery metadata once to the receiver endpoint. Default: `true`.

### Configuration validation

The plugin enforces these rules:

- `receiver_url` must use `http` or `https`.
- `receiver_url` must target `localhost` or a private local network IP address.
- Polling interval values below 5 minutes are automatically adjusted to 5 minutes.

## Runtime behavior

### First launch discovery

On first launch, the integration:

1. Loads any previously saved metadata from the Home Assistant config directory.
2. If no metadata exists, it queries both the entity registry and the state registry.
3. Builds a metadata table describing each discovered entity, including:
   - `device_id`
   - `entity_id`
   - `friendly_name`
   - `domain`
   - `current_value`
   - `unit_of_measurement`
   - `data_type`
   - `writeable` capability
   - `supported_services`
4. Saves the metadata to a local JSON file.
5. Optionally sends the metadata payload once to the configured local receiver endpoint.

### Polling and change detection

After startup, the integration:

1. Initializes a snapshot of current entity states.
2. Uses `SensorReaderCoordinator` to poll entity states every configured interval.
3. Compares current states against the last snapshot.
4. Sends only changed values to the receiver endpoint.
5. Updates the last snapshot after successful delivery.

### Delivery

The plugin uses `aiohttp` via Home Assistant's `async_get_clientsession`.

Delivery behavior includes:

- retry attempts (default 3)
- exponential backoff between retries
- logging of failures and successes
- warning on failed initial metadata delivery, but continuing startup

## Code details and comments

### `manifest.json`

Defines integration metadata and indicates a local polling integration with `iot_class: local_polling`.

### `const.py`

Stores domain and configuration constants, default URLs, polling intervals, filenames, and shared keys.

### `helpers.py`

Contains:

- `validate_receiver_url(url)` — ensures local-only HTTP(S) addresses.
- `validate_poll_interval(value)` — enforces minimum interval and converts to integer.
- `is_local_address(hostname)` — recognizes `localhost`, loopback, and private IPs.
- `load_metadata(hass)` / `save_metadata(hass, metadata)` — local metadata persistence helpers.
- `build_metadata_record(state, entity_entry)` — generates rich entity metadata.
- `build_change_payload(current_snapshot, previous_snapshot)` — computes only changed values.

### `discovery.py`

Performs first-run discovery using Home Assistant state registry and entity registry to build a metadata table.

### `sender.py`

Sends payloads to the configured local endpoint, with retries and error logging. It is designed to handle failed delivery gracefully while preserving the plugin's runtime.

### `coordinator.py`

Implements the Home Assistant `DataUpdateCoordinator` pattern for scheduled polling. It collects current states, generates change payloads, and triggers delivery.

### `config_flow.py`

Implements the Home Assistant configuration flow, including options flow for runtime changes. It validates the receiver URL and polling interval before creating or updating the config entry.

### `__init__.py`

Bootstraps the integration. It handles:

- loading or discovering metadata,
- saving the metadata file,
- optionally sending initial metadata,
- creating and initializing the coordinator,
- handling config entry reloads and unloads.

## Local metadata storage

The plugin stores metadata in the Home Assistant config directory under:

- `sensor_reader_metadata.json`

This file is used to avoid repeated discovery on every startup unless the integration is reinstalled or explicitly refreshed.

## Notes for future development

- The plugin is intentionally modular; discovery, diffing, serialization, and posting logic are kept separate.
- Future features can include writing commands to devices, more advanced payload formats (CSV export), and support for additional device control endpoints.
- Logging is designed to expose discovery summaries, change payload details, and endpoint delivery status.

## Next steps

1. Deploy the integration into Home Assistant.
2. Configure the local receiver service and confirm the endpoint is reachable.
3. Add the integration through Home Assistant's UI.
4. Verify initial metadata discovery and change-reporting behavior.

---

`homeassistantplugin/homeassistant_sensor_reader` is the full plugin package for Home Assistant. Use this README as the central reference for installation and runtime behavior.