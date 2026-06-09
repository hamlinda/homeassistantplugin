import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

_LOGGER = logging.getLogger(__name__)

CREATE_DEVICE_METADATA_TABLE = """
CREATE TABLE IF NOT EXISTS device_metadata (
    entity_id TEXT PRIMARY KEY,
    device_id TEXT,
    friendly_name TEXT,
    domain TEXT,
    unit_of_measurement TEXT,
    writeable INTEGER,
    supported_services TEXT,
    state_attributes TEXT,
    last_updated TEXT
)
"""

CREATE_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS sensor_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    device_id TEXT,
    entity_id TEXT NOT NULL,
    friendly_name TEXT,
    domain TEXT,
    old_state TEXT,
    new_state TEXT,
    unit_of_measurement TEXT,
    attributes TEXT,
    payload_type TEXT
)
"""

CREATE_HISTORY_INDEX = """
CREATE INDEX IF NOT EXISTS idx_sensor_history_entity_timestamp
ON sensor_history(entity_id, timestamp)
"""


class LocalDataStore:
    """Manage storage for sensor change history and metadata."""

    def __init__(self, db_path: Path, csv_path: Path):
        self.db_path = db_path
        self.csv_path = csv_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_database(self) -> None:
        with self._get_connection() as conn:
            conn.execute(CREATE_DEVICE_METADATA_TABLE)
            conn.execute(CREATE_HISTORY_TABLE)
            conn.execute(CREATE_HISTORY_INDEX)
            conn.commit()
        _LOGGER.debug("Initialized local storage database at %s", self.db_path)

    def save_metadata_items(self, metadata_items: List[Dict[str, Any]]) -> None:
        """Persist device metadata records for future retrieval."""
        if not metadata_items:
            return

        with self._get_connection() as conn:
            for item in metadata_items:
                conn.execute(
                    """
                    INSERT INTO device_metadata (
                        entity_id,
                        device_id,
                        friendly_name,
                        domain,
                        unit_of_measurement,
                        writeable,
                        supported_services,
                        state_attributes,
                        last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(entity_id) DO UPDATE SET
                        device_id=excluded.device_id,
                        friendly_name=excluded.friendly_name,
                        domain=excluded.domain,
                        unit_of_measurement=excluded.unit_of_measurement,
                        writeable=excluded.writeable,
                        supported_services=excluded.supported_services,
                        state_attributes=excluded.state_attributes,
                        last_updated=excluded.last_updated
                    """,
                    (
                        item.get("entity_id"),
                        item.get("device_id"),
                        item.get("friendly_name"),
                        item.get("domain"),
                        item.get("unit_of_measurement"),
                        int(bool(item.get("writeable"))),
                        json.dumps(item.get("supported_services", [])),
                        json.dumps(item.get("state_attributes", {})),
                        datetime.utcnow().isoformat(),
                    ),
                )
            conn.commit()
        _LOGGER.debug("Saved %s metadata records", len(metadata_items))

    def save_sensor_changes(self, change_items: List[Dict[str, Any]]) -> None:
        """Append changed sensor readings into the history store."""
        if not change_items:
            return

        timestamp = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            for item in change_items:
                conn.execute(
                    """
                    INSERT INTO sensor_history (
                        timestamp,
                        device_id,
                        entity_id,
                        friendly_name,
                        domain,
                        old_state,
                        new_state,
                        unit_of_measurement,
                        attributes,
                        payload_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.get("timestamp", timestamp),
                        item.get("device_id"),
                        item.get("entity_id"),
                        item.get("friendly_name"),
                        item.get("domain"),
                        item.get("old_state"),
                        item.get("new_state"),
                        item.get("unit_of_measurement"),
                        json.dumps(item.get("attributes", {})),
                        item.get("payload_type", "sensor_changes"),
                    ),
                )
            conn.commit()
        _LOGGER.debug("Persisted %s sensor change records", len(change_items))

    def query_history(
        self,
        entity_id: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query sensor change history with optional filters and pagination."""
        sql = "SELECT * FROM sensor_history"
        params: List[Any] = []
        filters: List[str] = []

        if entity_id:
            filters.append("entity_id = ?")
            params.append(entity_id)

        if start:
            filters.append("timestamp >= ?")
            params.append(start)

        if end:
            filters.append("timestamp <= ?")
            params.append(end)

        if filters:
            sql += " WHERE " + " AND ".join(filters)

        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def query_devices(self) -> List[Dict[str, Any]]:
        """Retrieve persisted device metadata and supporting values."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM device_metadata ORDER BY entity_id").fetchall()
        return [self._row_to_dict(row) for row in rows]

    def append_csv(self, change_items: List[Dict[str, Any]]) -> None:
        """Append change records to a CSV file for easy export and backup."""
        import csv

        headers = [
            "timestamp",
            "device_id",
            "entity_id",
            "friendly_name",
            "domain",
            "old_state",
            "new_state",
            "unit_of_measurement",
            "attributes",
            "payload_type",
        ]
        timestamp = datetime.utcnow().isoformat()

        file_exists = self.csv_path.exists()
        with self.csv_path.open("a", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL)
            if not file_exists:
                writer.writerow(headers)
            for item in change_items:
                writer.writerow(
                    [
                        item.get("timestamp", timestamp),
                        item.get("device_id"),
                        item.get("entity_id"),
                        item.get("friendly_name"),
                        item.get("domain"),
                        item.get("old_state"),
                        item.get("new_state"),
                        item.get("unit_of_measurement"),
                        json.dumps(item.get("attributes", {})),
                        item.get("payload_type", "sensor_changes"),
                    ]
                )
        _LOGGER.debug("Appended %s rows to CSV history file %s", len(change_items), self.csv_path)

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        record = dict(row)
        if record.get("attributes"):
            try:
                record["attributes"] = json.loads(record["attributes"])
            except json.JSONDecodeError:
                record["attributes"] = record["attributes"]
        if record.get("supported_services"):
            try:
                record["supported_services"] = json.loads(record["supported_services"])
            except json.JSONDecodeError:
                record["supported_services"] = record["supported_services"]
        return record
