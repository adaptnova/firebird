"""Trace Collector - Captures and stores agent execution traces."""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4

import asyncpg
from temporalio.client import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TraceCollector:
    """Collects execution traces from Temporal and stores them for analysis."""

    def __init__(self, postgres_uri: str, temporal_host: str = "localhost:7233"):
        self.postgres_uri = postgres_uri
        self.temporal_host = temporal_host
        self.temporal_client = None

    async def connect(self):
        """Connect to Temporal and PostgreSQL."""
        self.temporal_client = await Client.connect(self.temporal_host)
        logger.info(f"Connected to Temporal at {self.temporal_host}")

    async def create_tables(self):
        """Create database tables for storing traces."""
        conn = await asyncpg.connect(self.postgres_uri)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_executions (
                id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                task_description TEXT,
                status TEXT,  -- completed, failed, timeout
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration_seconds FLOAT,
                tool_calls JSONB,  -- List of all tool calls made
                input_messages JSONB,
                output_messages JSONB,
                error_message TEXT,
                metadata JSONB,  -- Additional metadata
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tool_executions (
                id TEXT PRIMARY KEY,
                execution_id TEXT REFERENCES agent_executions(id),
                tool_name TEXT NOT NULL,
                input_params JSONB,
                output_result JSONB,
                execution_time_seconds FLOAT,
                success BOOLEAN,
                error TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_executions_agent_type
            ON agent_executions(agent_type)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_executions_status
            ON agent_executions(status)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_executions_created
            ON agent_executions(created_at DESC)
        """)

        await conn.close()
        logger.info("Database tables created successfully")

    async def collect_workflow_trace(self, workflow_id: str, run_id: str) -> Optional[Dict[str, Any]]:
        """Collect trace from a Temporal workflow execution."""
        if not self.temporal_client:
            await self.connect()

        try:
            # Get workflow handle
            handle = self.temporal_client.get_workflow_handle(workflow_id, run_id)

            # Get workflow execution info
            desc = await handle.describe()

            # Try to get result (if completed)
            try:
                result = await handle.result()
            except Exception as e:
                result = None
                error = str(e)

            # Get event history
            history = await handle.fetch_history()

            # Extract tool calls and other relevant info from history
            tool_calls = []
            error_message = None
            status = "completed"

            for event in history.events:
                if event.event_type == 4:  # ACTIVITY_TASK_SCHEDULED
                    activity_data = event.activity_task_scheduled_event_attributes
                    tool_calls.append({
                        "activity_type": activity_data.activity_type.name,
                        "input": activity_data.input.payloads[0].data.decode('utf-8') if activity_data.input.payloads else None,
                    })

                elif event.event_type == 20:  # WORKFLOW_EXECUTION_FAILED
                    status = "failed"
                    error_message = event.workflow_execution_failed_event_attributes.failure.message

                elif event.event_type == 21:  # WORKFLOW_EXECUTION_TIMED_OUT
                    status = "timeout"

            trace = {
                "workflow_id": workflow_id,
                "run_id": run_id,
                "status": status,
                "start_time": desc.raw.execution_time.ToDatetime(),
                "end_time": desc.raw.close_time.ToDatetime() if desc.raw.close_time else None,
                "duration_seconds": (desc.raw.close_time.ToDatetime() - desc.execution_time.ToDatetime()).total_seconds() if desc.raw.close_time else None,
                "tool_calls": tool_calls,
                "result": result,
                "error_message": error_message,
                "task_queue": desc.raw.task_queue,
            }

            logger.info(f"Collected trace for workflow {workflow_id}")
            return trace

        except Exception as e:
            logger.error(f"Failed to collect trace for {workflow_id}: {e}")
            return None

    async def store_execution(
        self,
        agent_type: str,
        task_description: str,
        trace: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store execution trace in PostgreSQL."""
        conn = await asyncpg.connect(self.postgres_uri)

        execution_id = str(uuid4())

        # Extract tool calls for separate table
        tool_calls_json = json.dumps(trace.get("tool_calls", []))

        await conn.execute("""
            INSERT INTO agent_executions (
                id, workflow_id, run_id, agent_type, task_description,
                status, start_time, end_time, duration_seconds,
                tool_calls, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """, execution_id, trace["workflow_id"], trace["run_id"],
           agent_type, task_description, trace["status"],
           trace["start_time"], trace["end_time"], trace["duration_seconds"],
           tool_calls_json, json.dumps(metadata or {}))

        # Store individual tool executions
        for i, tool_call in enumerate(trace.get("tool_calls", [])):
            tool_id = f"{execution_id}_{i}"
            await conn.execute("""
                INSERT INTO tool_executions (
                    id, execution_id, tool_name, input_params
                ) VALUES ($1, $2, $3, $4)
            """, tool_id, execution_id, tool_call.get("activity_type", "unknown"),
               tool_call.get("input", {}))

        await conn.close()
        logger.info(f"Stored execution {execution_id} for {agent_type}")
        return execution_id

    async def collect_all_recent(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Collect all recent executions."""
        conn = await asyncpg.connect(self.postgres_uri)

        rows = await conn.fetch("""
            SELECT * FROM agent_executions
            WHERE created_at > NOW() - INTERVAL '$1 hours'
            ORDER BY created_at DESC
        """, hours)

        await conn.close()
        return [dict(row) for row in rows]

    async def get_agent_executions(self, agent_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get executions for a specific agent type."""
        conn = await asyncpg.connect(self.postgres_uri)

        rows = await conn.fetch("""
            SELECT * FROM agent_executions
            WHERE agent_type = $1
            ORDER BY created_at DESC
            LIMIT $2
        """, agent_type, limit)

        await conn.close()
        return [dict(row) for row in rows]


# Example usage
async def main():
    """Demo: Collect traces from recent Temporal workflows."""
    import os

    postgres_uri = os.environ.get("POSTGRES_CLUSTER_URLS")
    if not postgres_uri:
        logger.error("POSTGRES_CLUSTER_URLS not set")
        return

    collector = TraceCollector(postgres_uri)
    await collector.connect()
    await collector.create_tables()

    # In a real scenario, you would get workflow IDs from your application
    # For demo, we're just creating the tables and showing the API

    logger.info("Trace Collector ready!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
