# Home Assistant Sensor Reader & Local Data Receiver

## Overview

This project contains the planning and architecture for a two-part optimized solution:

1. A Home Assistant integration/plugin that discovers and queries all registered sensors and their readings.
2. A locally addressable web service that receives sensor change data from Home Assistant, stores it as history, and supports future runtime control and device configuration.

The initial focus is on discovery, change-only distribution, configurable intervals, and maintaining a runtime history of sensor values for evaluation and modification.

## Goals

- Discover every Home Assistant entity that can be read or modified during runtime.
- Generate a device/reading metadata table on first launch.
- Send only changed sensor values to a local endpoint.
- Support a user-configurable polling interval, defaulting to a minimum of 5 minutes.
- Store received data history and expose it for evaluations and future automation.
- Provide a clear execution interface for controlling different devices.

## Components

### 1. Home Assistant Plugin

The Home Assistant plugin will:

- Query the registry of devices and sensors on first launch.
- Build a metadata table with device IDs, entity IDs, friendly names, domains, current values, and writeable attributes.
- Persist the generated metadata locally and optionally cache it inside Home Assistant.
- Poll sensor values at an interval configured by the user.
- Detect and send only changed data in CSV or JSON format to a local web endpoint.
- Optionally publish discovered metadata once at startup for validation.

### 2. Local Data Receiver Web Interface

The local web interface will:

- Expose an HTTP endpoint for receiving POST submissions from Home Assistant.
- Accept a payload containing only changed sensor readings.
- Convert and store incoming data as CSV records or in a structured history store.
- Maintain time series history for each sensor and device.
- Support future configuration of complex device actions and combinations.

## Execution Workflow

1. Install the Home Assistant plugin.
2. Configure the local receiver endpoint address and polling interval.
3. On first launch, the plugin discovers all registered sensors and generates the metadata table.
4. The plugin sends the metadata table to the local receiver endpoint once.
5. The plugin polls all sensors at the configured interval.
6. For each interval, only changed readings are compiled and sent.
7. The receiver stores the changes and persists them for later analysis.

## Streamlined Operations

The system will support functions such as:

- `initialize_discovery()` — discover all sensors and build the metadata table.
- `send_metadata_table()` — post initial device and reading table to the local endpoint.
- `poll_changes()` — check for changed sensor values at runtime.
- `prepare_change_payload()` — serialize changed items as CSV/JSON.
- `post_updates()` — send changed data to the local web service.
- `receive_and_store()` — ingest POST payload and append to history.
- `query_history(sensor_id, window)` — retrieve historical values for evaluation.
- `run_device_function(device_id, action, params)` — trigger a configured operation in future phases.

## Configuration

Core configurable settings will include:

- `receiver_endpoint`: local URL for webhook delivery.
- `poll_interval_minutes`: polling frequency, default 5 minutes, minimum 5.
- `initial_discovery_enabled`: run discovery on first launch.
- `history_storage_path`: local path for CSV or database storage.
- `change_filter`: optional list of entity domains or IDs to include/exclude.

## Future Directions

Future behavior and expansion will include:

- Complex device setting combinations and multi-device scenarios.
- Rules-based actions triggered by history patterns.
- User interface for reviewing history, editing values, and scheduling updates.
- Runtime command execution across groups of devices.
- Enriched metadata for custom sensor capabilities and writeback support.

## Documentation

This repository stores:

- `README.md` — planning and high level component overview.
- `architecture.md` — detailed architecture, component interactions, and known challenges.

## Next Steps

- Define the Home Assistant integration manifest and onboarding logic.
- Design the local web receiver service API and storage schema.
- Implement the discovery routine, change diffing, and payload serializer.
- Add security controls for local endpoint access and data integrity.
- Build test cases for discovery, change detection, and history persistence.

---

## ⚠️ Disclaimer

This repository may reference, integrate, or build upon third-party software, libraries, frameworks, or tools. Such references do not imply ownership, endorsement, or affiliation with those projects. All third-party software remains the property of its respective authors and is subject to its own license terms.

**Use of any code in this repository is entirely at your own risk.** No warranties, guarantees, or assurances of any kind are provided — express or implied — regarding fitness for purpose, security, reliability, or correctness. The author(s) of this repository accept no liability for any damages, losses, or issues arising from the use of this code or any third-party dependencies it references.

Always review third-party licenses and conduct your own due diligence before using any software in production environments.
