# Architecture Overview

## System Architecture

The solution is divided into two core services:

1. **Home Assistant Plugin**
2. **Local Data Receiver Web Service**

These components communicate over a local HTTP interface and are designed to minimize network load by sending only changed sensor data.

## Component Breakdown

### Home Assistant Plugin

Responsibilities:

- Discover all registered devices, entities, sensors, and writeable values.
- Build an initial metadata table describing:
  - device identifiers
  - entity identifiers
  - domain types
  - friendly names
  - current values
  - available services and writeable attributes
- Persist metadata locally after first discovery.
- Regularly poll the sensor state registry with a user-configurable interval.
- Detect changes compared to the last sent snapshot.
- Serialize changed values to a compact payload.
- POST changes to the local receiver endpoint.

Key design decisions:

- Use first-run discovery to reduce repeated enumeration overhead.
- Cache the metadata table to avoid extra startup delay.
- Apply a minimum polling rate of 5 minutes to limit load.
- Use change-only distribution to reduce payload volume and processing.

### Local Data Receiver Web Service

Responsibilities:

- Expose a local HTTP POST endpoint for incoming sensor updates.
- Validate and normalize incoming payloads.
- Store each record into a history data store.
- Preserve timestamps and sensor metadata for audit and analysis.
- Expose a query interface for history and future control operations.
- Optionally serve a simple local web UI for monitoring and configuration.

Key design decisions:

- Store history as CSV or structured JSON to support evaluation and migration.
- Keep the endpoint local to improve privacy and reduce external dependencies.
- Accept only changed values to simplify storage and minimize write operations.
- Use lightweight storage for fast writes and easy export.

## Data Flow

1. On first startup, plugin calls `discover_entities()`.
2. It generates `metadata_table.csv` and optionally sends this to the local receiver.
3. At each poll interval, plugin compares current state to last-known state.
4. It builds a delta payload containing only changed sensor readings.
5. Plugin POSTs the delta payload to `http://localhost:<port>/sensor-updates`.
6. Receiver validates and appends data to the history store.
7. Analysis or evaluation tools read from the stored history.

## Interfaces

### Plugin to Receiver API

- `POST /sensor-updates`
  - Payload: CSV or JSON list of changed readings
  - Fields:
    - `timestamp`
    - `device_id`
    - `entity_id`
    - `friendly_name`
    - `domain`
    - `attribute`
    - `old_value`
    - `new_value`
    - `unit`
    - `quality`

- `POST /device-metadata`
  - Initial discovery metadata upload.
  - Fields describe read/write capabilities and current status.

### Local Receiver API (future)

- `GET /history` — query stored sensor history.
- `GET /devices` — list discovered devices and recent values.
- `POST /execute` — trigger configured device functions or automation.
- `POST /config` — adjust retention, filtering, or evaluation settings.

## Storage Model

### Minimal viable store

- File-based CSV history
- Each row contains a timestamp and changed value metadata
- Easy to export and analyze with common tools

### Extended storage model

- SQLite or light database for history queries
- Index on `timestamp`, `device_id`, `entity_id`
- Separate metadata table for device definitions and capabilities
- Retention policy to control growth over time

## Execution Operations

The architecture supports clearly defined operations:

- `initialize_discovery()` — builds the sensor map and metadata table.
- `send_initial_metadata()` — emits the discovery payload once.
- `poll_sensor_changes()` — collects current state and computes diffs.
- `publish_changes()` — transmits changed readings only.
- `receive_payload()` — endpoint logic validates and stores incoming data.
- `archive_history()` — periodic snapshot or cleanup of stored history.
- `execute_device_action()` — future extension to run operations on specific devices.
- `schedule_combination()` — orchestrate multi-device setting updates.

## Security & Locality

- Keep the web service bound to `localhost`.
- Use local endpoint authentication if the runtime environment can support it.
- Validate payload schema before storage.
- Avoid exposing the endpoint to external networks.

## Known Challenges

### Discovery and metadata management

- Home Assistant entity registry changes over time.
- New devices may appear after first launch and require re-discovery.
- Not all entities expose clear writeable attributes.

### Change detection and noise

- Sensor values may fluctuate frequently due to noise or transient changes.
- The plugin must distinguish meaningful changes from insignificant jitter.
- Quick state changes can produce many update events.

### Performance and interval tuning

- Polling too frequently can overload Home Assistant and the receiver.
- Polling too infrequently can miss meaningful state transitions.
- Default interval of 5 minutes balances responsiveness and efficiency.

### History storage

- Storing every change increases disk usage over time.
- CSV storage is easy but may be inefficient for large datasets.
- Retention policies and pruning will be necessary for long-term use.

### Device control and complex operations

- Combining device commands across models and brands adds complexity.
- Future automation must safely handle conflicts and dependencies.
- Careful validation is required before applying runtime modifications.

## Future Architecture Extensions

- Add an event-driven listener mode to capture state changes directly.
- Add rules engine support for complex combinations of device settings.
- Provide a UI for users to define device groups and execution sequences.
- Implement a configurable history retention and analytics dashboard.
- Extend support for remote or cloud-synced device control if needed.

## Summary

This architecture is optimized for local execution, efficient change distribution, and maintainable history storage. It is designed to support future expansion toward advanced control, evaluation, and user-driven device configuration.