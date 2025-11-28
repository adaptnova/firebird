# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 🚀 Common Commands

### Setup & Installation
```bash
# Install dependencies
uv sync

# Test all infrastructure (Phase 1)
cd core/databases && python test_all.py
cd ../message_bus && python test_all.py
```

### Running Agents
```bash
# Run Research Agent demo (parallel web search)
python agents/research/src/autonomous_research_swarm.py

# Run specific research topic
uv run python agents/research/src/research_agent.py "quantum computing"
```

### Database Testing
```bash
# Test all 8 databases
cd core/databases && python test_all.py

# Individual DB tests
psql -h localhost -p 18030 -c "SELECT 1"  # PostgreSQL
curl http://localhost:18050/health         # Qdrant
mongosh --port 18070 --eval "db.adminCommand('ping')"  # MongoDB
```

### Message Bus Testing
```bash
# Test all 3 message buses
cd core/message_bus && python test_all.py

# Individual bus checks
curl http://localhost:8080/admin/v2/brokers  # Pulsar
rpk cluster info --brokers 127.0.0.1:18020  # RedPanda
nats-server --version                        # NATS
```

### Research Workflows
```bash
# Run temporal research workflows
python temporal_research_workflows.py
python temporal_research_workflows_v2.py

# Convert reports
python convert_reports.py
```

### Monitoring & Health Checks
```bash
# Grafana Dashboard
open http://localhost:18031

# Temporal UI
open http://localhost:8080

# Check agent health
curl http://localhost:8000/health/research
curl http://localhost:8000/health/monitor
```

---

## 🏗️ Architecture Overview

### System Architecture
```
┌─────────────────────────────────────────┐
│  SLACK BOT     │ GRAFANA DASHBOARD      │
│  (HITL I/O)    │  (Real-time Metrics)   │
└────────┬────────┴────────┬──────────────┘
         │                 │
         └─────────────────┘
                    │
                    ▼
         ┌──────────────────────────┐
         │   AGENT REGISTRY         │
         │  (5 Agents Active)       │
         └───────────┬──────────────┘
                     │
         ┌───────────┴──────────────┐
         │                          │
         ▼                          ▼
┌────────────────┐         ┌────────────────┐
│ MESSAGE BUS    │         │  8 DATABASES   │
│ (RedPanda +    │         │ (PostgreSQL,   │
│  Pulsar +      │         │  Qdrant,       │
│  NATS)         │         │  MongoDB, etc.)│
└────────────────┘         └────────────────┘
```

### Key Components

#### 1. **Agent Registry** (`agent_registry/agents.yaml`)
- Central registry for 5 agents: research, analysis, creative, monitor, code
- Defines capabilities, APIs, databases, and routing rules
- Health check endpoints for each agent
- Agent-to-agent workflow routing configuration

#### 2. **Core Infrastructure** (`core/`)
- **databases/**: 8 database connectors (PostgreSQL, Qdrant, MongoDB, Neo4j, ClickHouse, QuestDB, DragonflyDB, Redis)
- **message_bus/**: 3 message buses (RedPanda, Pulsar, NATS)
- **orchestration/**: LangGraph + Temporal integration (planned)
- **llm_providers/**: 6+ LLM integrations (Groq, Moonshot, MiniMax, z.ai, Hugging Face)
- **search_apis/**: 7+ search APIs (Perplexity, Brave, Jina, Firecrawl, Serper, Tavily, Algolia)

#### 3. **Agents** (`agents/`)
- **research/**: Autonomous researcher with parallel web search
- **analysis/**: Synthesizes research into insights
- **creative/**: Generates reports and content
- **monitor/**: 24/7 monitoring and anomaly detection
- **code/**: Autonomous software development

#### 4. **Reports & Updates** (`reports/`, `updates/`)
- Agent-generated content stored in JSON format
- Daily/weekly summaries and metrics
- Research findings and insights

---

## 🗄️ Database Architecture

### Database Responsibilities
- **PostgreSQL + TimescaleDB** (port 18030): Structured data, time-series metrics
- **Qdrant** (18050): Vector embeddings for RAG and semantic search
- **MongoDB** (18070): Documents, agent knowledge, reports
- **Neo4j** (18060-61): Relationships and knowledge graphs
- **ClickHouse** (18090): Real-time analytics and aggregations
- **QuestDB** (18091): High-frequency time-series data
- **DragonflyDB** (18000-02): High-performance cache (3 nodes)
- **Redis Cluster** (18010-12): Distributed cache and sessions

### Connection Pattern
```python
# PostgreSQL example
import asyncpg
conn = await asyncpg.connect('postgresql://postgres_admin_user:***@localhost:18030/teamadapt')
result = await conn.fetchval('SELECT 1')

# Qdrant example
import requests
response = requests.get('http://localhost:18050/health')

# MongoDB example
from pymongo import MongoClient
client = MongoClient('mongodb://admin:***@localhost:18070/admin')
result = client.admin.command('ping')
```

---

## 📨 Message Bus Pattern

### Three Message Buses
1. **RedPanda** (localhost:18020): Kafka-compatible, high throughput event streaming
2. **Pulsar** (localhost:8080): Pub/Sub for real-time messaging
3. **NATS** (localhost:18020): Lightweight agent-to-agent communication

### Usage Pattern
```python
# Event Publishing
producer.send('firebird.research.request', {
    'topic': 'quantum computing',
    'timestamp': time.time()
})

# Agent Communication via NATS
await nc.publish("agents.research", b"Hello Research Agent!")
```

---

## 🤖 Agent System

### Active Agents (5)
1. **Research Agent** (`firebird-research-v1`)
   - Capabilities: web_search, deep_research, data_synthesis, source_verification
   - APIs: tavily, brave, perplexity, serper
   - Databases: MongoDB (storage), Qdrant (embeddings)

2. **Analysis Agent** (`firebird-analysis-v1`)
   - Capabilities: pattern_recognition, trend_identification, risk_assessment
   - LLM: Moonshot
   - Databases: PostgreSQL, ClickHouse, Neo4j

3. **Creative Agent** (`firebird-creative-v1`)
   - Capabilities: report_generation, presentation_creation, content_writing
   - LLM: Groq
   - Databases: MongoDB

4. **Monitor Agent** (`firebird-monitor-v1`)
   - Capabilities: keyword_monitoring, competitor_tracking, anomaly_detection
   - Databases: QuestDB, ClickHouse, Dragonfly
   - Health check interval: 10s (more frequent)

5. **Code Agent** (`firebird-code-v1`)
   - Capabilities: feature_implementation, bug_fixing, code_review
   - LLM: MiniMax
   - GitHub integration: enabled

### Agent Workflows
- **research_topic**: monitor → research
- **completed_research**: research → analysis
- **completed_analysis**: analysis → creative
- **code_issue**: monitor → code
- **emergency**: any → monitor → slack_notification

---

## 🔍 Research Workflows

### Example: Autonomous Research Swarm
**File**: `agents/research/src/autonomous_research_swarm.py`

Runs 20 parallel research workers, each investigating a specific topic about Temporal and AI agents. Key features:
- Parallel execution using `asyncio.gather()`
- Tavily API for deep research
- Automatic report generation in JSON format
- Executive summary compilation

**Usage**:
```bash
python agents/research/src/autonomous_research_swarm.py
```

**Output**: 20+ research reports saved to `reports/research_worker_*.json`

### Temporal Workflows
**Files**: `temporal_research_workflows.py`, `temporal_research_workflows_v2.py`

Implements crash-proof workflows using Temporal's durable execution pattern:
- Workflows survive process crashes
- Automatic retry with backoff
- State persistence between steps
- Activities for side effects (API calls, DB writes)

### Report Conversion
**File**: `convert_reports.py`

Converts JSON research reports to markdown format for readability.

---

## 📊 Monitoring & Observability

### Grafana Dashboard
- **URL**: http://localhost:18031
- **Metrics Tracked**:
  - Active agents (5/5)
  - Tasks completed
  - Success rate
  - Message bus activity
  - Database health

### Temporal UI
- **URL**: http://localhost:8080
- **Purpose**: Visualize workflow execution, retry history, and task queues

### Health Check Endpoints
Each agent exposes a `/health/{agent_name}` endpoint:
- research: 30s interval
- monitor: 10s interval (critical)
- analysis: 30s interval
- creative: 30s interval
- code: 30s interval

---

## 🔧 Development Workflow

### Testing Strategy
1. **Infrastructure Tests** (Phase 1 - 30 min):
   ```bash
   cd core/databases && python test_all.py
   cd ../message_bus && python test_all.py
   ```

2. **Agent Tests**:
   ```bash
   cd tests/unit && python -m pytest
   cd ../integration && python -m pytest
   ```

3. **End-to-End Tests**:
   ```bash
   cd tests/e2e && python test_autonomous_workflow.py
   ```

### Best Practices
- **Type Safety**: Use Pydantic models for all data structures
- **Durability**: Every workflow uses Temporal for crash-proof execution
- **Parallelism**: Use `async/await` with `asyncio.gather()` or `asyncio.TaskGroup()`
- **Self-Documenting**: Comprehensive docstrings explaining "why" not "what"
- **Security**: No hardcoded secrets, use environment variables
- **Testing**: 100% coverage including unit, integration, and e2e tests

### Key Patterns
```python
# Async parallel execution
async def parallel_research(topics):
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(research_topic(t)) for t in topics]
    return [task.result() for task in tasks]

# Temporal workflow
@workflow.defn
class ResearchWorkflow:
    @workflow.run
    async def run(self, topic: str):
        result = await workflow.execute_activity(search_activity, topic)
        return result

# Database connection with pooling
async with self.pool.acquire() as conn:
    return await conn.fetch(sql)
```

---

## 🔑 Environment & Configuration

### Required Environment Variables
```bash
GROQ_API_KEY=${GROQ_API_KEY}
PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY}
# ... other API keys as needed
```

### Service Ports
- PostgreSQL: 18030
- Qdrant: 18050
- MongoDB: 18070
- Neo4j: 18060-61
- ClickHouse: 18090
- QuestDB: 18091
- DragonflyDB: 18000-02
- Redis: 18010-12
- RedPanda: 18020
- Pulsar: 8080
- NATS: 18020
- Grafana: 18031
- Temporal: 7233 (server), 8080 (UI)

### Configuration Files
- `agent_registry/agents.yaml`: Agent definitions and routing
- `configs/`: Environment-specific configurations
- `core/databases/*/connection.py`: Database connection configs
- `core/message_bus/client.py`: Message bus client

---

## 📁 Key Files & Directories

### Critical Files
- **`README.md`**: Project overview and quick start
- **`IMPLEMENTATION_PLAN.md`**: Phase-by-phase implementation timeline
- **`docs/best_practices.md`**: Development guidelines and patterns
- **`agent_registry/agents.yaml`**: Agent registry and routing rules
- **`core/databases/test_all.py`**: Database connectivity tests
- **`core/message_bus/test_all.py`**: Message bus connectivity tests

### Agent Implementations
- **`agents/research/src/autonomous_research_swarm.py`**: Main research agent with 20 parallel workers
- **`research_worker.py`**: Research worker entry point
- **`bleeding_edge_worker.py`**: Experimental agent features
- **`temporal_research_workflows.py`**: Temporal workflow implementation v1
- **`temporal_research_workflows_v2.py`**: Temporal workflow implementation v2

### Reports & Outputs
- **`reports/`**: All agent-generated reports in JSON format
- **`updates/`**: Daily summaries, metrics, and status updates
- **`tasks/`**: HITL (Human-in-the-Loop) task tracking

### Operations
- **`ops/ops_history.md`**: Complete operation log
- **`scripts/`**: Deployment and monitoring scripts
- **`cloud/`**: Cloud deployment configurations

---

## 🎯 Current Status

### Infrastructure: ✅ Complete (19/19 Services)
- 8 Databases operational
- 3 Message buses running
- 6+ LLM providers configured
- 7+ Search APIs integrated
- Temporal server running
- Grafana monitoring active

### Development Phase
See `IMPLEMENTATION_PLAN.md` for current phase:
- Phase 1: Foundation (message bus + database connectivity)
- Phase 2: Orchestration (LangGraph + Temporal)
- Phase 3: Enhanced Research Agent
- Phase 4: Slack + Grafana integration
- Phase 5: All agents + workflows

### Recent Activity
- Research swarm executed successfully (20 parallel workers)
- Multiple research reports generated in `/reports/`
- Executive summaries created
- Temporal workflows tested and refined

---

## 💡 Tips for Development

1. **Start with infrastructure tests** - Verify all databases and message buses before running agents
2. **Use the Research Agent as reference** - `agents/research/src/autonomous_research_swarm.py` demonstrates best practices
3. **Follow routing patterns** - Agent workflows are defined in `agent_registry/agents.yaml`
4. **Monitor via Grafana** - Real-time metrics at http://localhost:18031
5. **Debug workflows via Temporal UI** - http://localhost:8080
6. **Check `docs/best_practices.md`** - Comprehensive guidelines for agent development
7. **Leverage parallel execution** - Use async/await throughout for performance
8. **Persist state via Temporal** - All workflows must be crash-proof
9. **Store results in appropriate databases** - Follow the schema defined per agent
10. **Update agent registry** - When adding new agents, update `agent_registry/agents.yaml`

---

## 🔗 Useful Links

- **Project README**: `/adapt/projects/firebird/README.md`
- **Implementation Plan**: `/adapt/projects/firebird/IMPLEMENTATION_PLAN.md`
- **Best Practices**: `/adapt/projects/firebird/docs/best_practices.md`
- **Architecture Overview**: `/adapt/projects/firebird/ARCHITECTURE/00_OVERVIEW.md`
- **Directory Structure**: `/adapt/projects/firebird/DIRECTORY_STRUCTURE.md`
- **Grafana Dashboard**: http://localhost:18031
- **Temporal UI**: http://localhost:8080

---

**Last Updated**: 2025-11-27
**Status**: Foundation Complete ✅
