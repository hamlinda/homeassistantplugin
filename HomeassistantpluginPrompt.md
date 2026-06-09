# Home Assistant Plugin Development Prompt

Use this prompt to initiate development of the Home Assistant plugin component.

## Objective
Build a Home Assistant integration that:  
- Discovers all registered sensors, entities, and runtime-modifiable values on first launch.  
- Generates a metadata table of devices and readings.  
- Polls for changes at a user-configurable interval.  
- Sends only changed sensor data to a locally addressable endpoint.  
- Uses a default interval of 5 minutes, with no allowed interval shorter than 5 minutes.

## Requirements

### Discovery and metadata generation
- Query the entity registry and state registry on first startup.
- Capture all entities, including devices and sensors, with these fields:
  - device ID
  - entity ID
  - friendly name
  - domain
  - current value
  - unit of measurement
  - data type
  - writeable capability / supported services
- Store the metadata table locally so that discovery runs once per install or when entities change.
- Optionally send the metadata table once to the local receiver endpoint to validate discovery.

### Change detection and delivery
- Poll sensor states at runtime using Home Assistant's scheduler.
- Compare current values against the last sent snapshot.
- Only send changed values to the local web service endpoint.
- Support a configurable polling interval setting in the integration configuration.
- Enforce a minimum interval of 5 minutes; if the user chooses a lower value, default to 5 minutes.
- Format change payloads as CSV or JSON as agreed with the receiver.
- Implement retries and error handling for local endpoint delivery.

### Local endpoint configuration
- Allow the user to configure the local endpoint URL, e.g. `http://localhost:8000/sensor-updates`.
- Support secure local addressing only (localhost or local network IP) and avoid external transmission.
- Provide configuration validation and user feedback in Home Assistant logs.

### Plugin architecture
- Use Home Assistant integration best practices.
- Create configuration schema, data update coordinator, and service registration.
- Keep logic modular: discovery, diffing, serialization, and posting separate.
- Support future extension for sending commands or metadata updates.

### Observability
- Log discovery results and change payload summaries.
- Log delivery success and failures.
- Track runtime state for the last successful send.

## Output
Deliver the following artifacts:
- Home Assistant integration code scaffold.
- Discovery and polling logic.
- Local endpoint configuration options.
- Snapshot and diffing mechanism.
- Example payload format for changed sensor values.
- README or doc snippets describing how to configure and run the plugin.

## Notes for the developer
- Prefer using Home Assistant core APIs and the entity registry.
- Keep the first-launch metadata discovery robust to dynamic device changes.
- Keep payloads small by sending change-only data.
- Make the solution easy to extend into runtime control and complex device operations later.
