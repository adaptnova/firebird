# MAS Ecosystem Naming Conventions

This document defines the naming standards for the Multi-Agent System (MAS) ecosystem to ensure consistency, discoverability, and effective tracing.

## Hierarchy & Structure

The hierarchy follows a `Division > Department > Team > Agent` structure.

### 1. Divisions
High-level organizational units.
*   **Format**: `div-[name]`
*   **Case**: Kebab-case
*   **Examples**: `div-engineering`, `div-marketing`, `div-operations`

### 2. Departments
Functional areas within a division.
*   **Format**: `dept-[division_short]-[name]`
*   **Case**: Kebab-case
*   **Examples**: `dept-eng-frontend`, `dept-mkt-content`, `dept-ops-security`

### 3. Teams
Groups of agents working on specific projects or domains.
*   **Format**: `team-[department_short]-[name]`
*   **Case**: Kebab-case
*   **Examples**: `team-fe-core-ui`, `team-sec-netsec`

### 4. Agents
Individual autonomous entities.
*   **Format**: `agent-[team_short]-[role]-[id]`
*   **Case**: Kebab-case
*   **Examples**: `agent-core-ui-builder-01`, `agent-netsec-analyst-05`

## Communication Channels (NATS/Redpanda)

### Subjects / Topics
*   **Broadcasts**: `broadcast.[division].[event_type]`
    *   Example: `broadcast.engineering.deployment_started`
*   **Direct Messages**: `dm.[agent_id].[target_agent_id]`
*   **Task Queues**: `tasks.[team].[priority]`
    *   Example: `tasks.team-fe-core-ui.high`
*   **Logs/Tracing**: `trace.[project_id].[component]`

## Identifiers (UUIDs)

All entities and events must be traceable via UUIDs.

*   **Project ID**: `proj-[uuid]`
*   **Session ID**: `sess-[uuid]` (Unique per interaction loop)
*   **Message ID**: `msg-[uuid]`
*   **Trace ID**: `trace-[uuid]` (Spans across microservices/agents)
*   **Handoff ID**: `handoff-[source_agent]-[target_agent]-[uuid]`

## Data Stores (DragonflyDB/Redis)

*   **Session State**: `session:{session_id}:state`
*   **Agent Memory**: `agent:{agent_id}:memory:{key}`
*   **Shared Context**: `project:{project_id}:context`

## File System

*   **Agent Workspace**: `/workspaces/[project_id]/[agent_id]/`
*   **Shared Assets**: `/shared/[project_id]/assets/`
