# Local Data Receiver Web Service Development Prompt

Use this prompt to initiate development of the local web service component.

## Objective
Build a locally addressable web interface that:  
- Receives POST submissions from the Home Assistant plugin.  
- Accepts a CSV or JSON payload of changed sensor data.  
- Stores a persistent history of sensor changes over time.  
- Supports future configuration of complex device setting combinations and control operations.

## Requirements

### Endpoint and payload handling
- Expose a local HTTP POST endpoint, for example `/sensor-updates`.
- Validate incoming payloads and reject invalid or malformed requests.
- Accept only changed sensor readings, not full state dumps.
- Support both CSV and JSON payload formats if needed, with a clear schema.
- Convert incoming payloads into a consistent internal record format.

### Storage and history
- Persist incoming sensor change data with timestamps.
- Store data as CSV, SQLite, or another lightweight local format.
- Ensure the history supports later evaluation, retrieval, and modification.
- Keep a record of device metadata, entity IDs, and the values sent.
- Support appending and indexing records for efficient queries.

### Future interface and operations
- Support retrieval of stored history through query APIs.
- Plan for future endpoints for executing device actions, e.g. `/execute`.
- Design the service to later accept complex combinations of device settings.
- Allow configuration of retention policies or history pruning.

### Architecture and usability
- Run as a local-only service bound to `localhost` by default.
- Provide clear logs for received uploads, validation, and storage status.
- Keep the service lightweight and easy to deploy.
- Document how the service can be started and configured locally.

### Security and reliability
- Restrict access to local network or localhost only.
- Validate all fields before persisting.
- Handle repeated delivery gracefully and avoid duplicate history rows if possible.
- Provide retry logic for transient ingestion failures.

## Output
Deliver the following artifacts:
- Local web service scaffold with endpoint definitions.
- Payload validation schema and parser.
- History storage implementation.
- Example queries or retrieval endpoints.
- Documentation for integrating the web service with the Home Assistant plugin.

## Notes for the developer
- Optimize the service for local evaluation and fast ingestion.
- Make storage extensible for future complex device action behaviors.
- Keep the API simple and easy to integrate with Home Assistant.
- Plan the service around local addressable endpoint reliability and privacy.
