# 🧬 IMMORTAL Quick Reference Guide

**Quick commands and examples for the self-improving agent system**

---

## 🚀 Quick Commands

### Run IMMORTAL

```bash
# Single learning cycle
cd /adapt/projects/firebird
python agents/immortal/orchestrator.py --mode single

# Continuous improvement (every 30 min)
python agents/immortal/orchestrator.py --mode continuous --interval 30

# Analysis only (no synthesis)
python agents/immortal/orchestrator.py --mode batch

# With custom database
python agents/immortal/orchestrator.py --mode single \
  --postgres "postgresql://user:pass@localhost:18030/firebird"
```

### Monitor Status

```bash
# Check tool registry
cat core/tool_registry/registry.json | jq '.tool_count'

# Check recent patterns
grep -r "pattern" agents/immortal/learning_engine/logs/ | tail -20

# View generated tools
ls -lh agents/immortal/tools/generated/
```

### Testing Components

```bash
# Test pattern detection
python -c "
import sys
sys.path.append('agents/immortal')
from tool_synthesis.pattern_detector import ToolPatternDetector
detector = ToolPatternDetector()
print('Pattern detector initialized')
"

# Test embeddings
python -c "
import sys
sys.path.append('agents/immortal')
from learning_engine.embedding_generator import EmbeddingGenerator
import asyncio
async def test():
    gen = EmbeddingGenerator()
    emb = await gen.aembed_query('test')
    print(f'Embedding shape: {len(emb)}')
asyncio.run(test())
"
```

---

## 💻 Python API Examples

### 1. Collect and Analyze Traces

```python
import asyncio
import sys
sys.path.append('/adapt/projects/firebird')

from agents.immortal.learning_engine import (
    TraceCollector,
    PatternAnalyzer
)

async def analyze():
    # Connect to database
    postgres_uri = "postgresql://localhost:18030/firebird"
    collector = TraceCollector(postgres_uri)

    # Collect recent executions
    executions = await collector.collect_all_recent(hours=1)
    print(f"Collected {len(executions)} executions")

    # Analyze patterns
    analyzer = PatternAnalyzer()
    analysis = await analyzer.analyze(executions)

    print(f"\nTool sequences found: {len(analysis['tool_sequences'])}")
    for seq in analysis['tool_sequences'][:3]:
        print(f"  - {' → '.join(seq['sequence'])} "
              f"({seq['frequency']} times)")

    print(f"\nSuccess factors:")
    for factor in analysis['success_factors']:
        print(f"  - {factor['description']}")

asyncio.run(analyze())
```

### 2. Detect and Generate Tools

```python
import asyncio
import sys
sys.path.append('/adapt/projects/firebird')

from agents.immortal.tool_synthesis import (
    ToolPatternDetector,
    ToolGenerator,
    ToolTestHarness
)

async def synthesize():
    # Example execution data
    executions = [
        {
            'workflow_id': 'wf1',
            'status': 'completed',
            'tool_calls': [
                {'activity_type': 'search_web'},
                {'activity_type': 'parse_html'},
                {'activity_type': 'extract_data'}
            ],
            'duration_seconds': 45
        }
    ] * 5  # Repeat 5 times

    # Detect patterns
    detector = ToolPatternDetector(threshold_frequency=3)
    report = detector.generate_synthesis_report(executions)

    print(f"Synthesis opportunities: {report['summary']}")

    # Generate tool
    for opp in report['opportunities']['high_priority'][:1]:
        generator = ToolGenerator()
        tool = generator.generate_combined_tool(
            tool_name=opp['tool_name'],
            tool_sequence=opp['tools'],
            pattern_context={
                'description': opp['rationale'],
                'success_rate': opp['success_rate'],
                'frequency': opp['frequency']
            }
        )

        print(f"\nGenerated tool: {tool['tool_name']}")
        print(f"File: {tool['file_path']}")

        # Test it
        harness = ToolTestHarness()
        test_result = harness.test_tool(tool['file_path'])
        print(f"Test result: {test_result['status']}")

asyncio.run(synthesize())
```

### 3. Query Pattern Hub

```python
import asyncio
import sys
sys.path.append('/adapt/projects/firebird')

from agents.immortal.learning_engine import EmbeddingGenerator

async def find_patterns():
    generator = EmbeddingGenerator()

    # Search for similar patterns
    patterns = await generator.search_similar_patterns(
        query="web search and data extraction",
        collection_name="tool_sequences",
        limit=3
    )

    for pattern in patterns:
        print(f"\nPattern (score: {pattern['score']:.3f}):")
        print(f"  Sequence: {' → '.join(pattern['payload']['sequence'])}")
        print(f"  Frequency: {pattern['payload']['frequency']}")
        print(f"  Success rate: {pattern['payload']['success_rate']:.1%}")

asyncio.run(find_patterns())
```

### 4. Publish Tool to Registry

```python
import asyncio
import sys
sys.path.append('/adapt/projects/firebird')

from agents.immortal.tool_synthesis import RegistryPublisher

async def publish():
    publisher = RegistryPublisher()

    # Create a simple tool file
    tool_code = '''
def example_tool(query: str) -> str:
    """Example tool that returns input."""
    return f"Result: {query}"
'''

    with open('/tmp/example_tool.py', 'w') as f:
        f.write(tool_code)

    # Publish to registry
    result = publisher.publish_tool(
        tool_info={
            'tool_name': 'example_tool',
            'file_path': '/tmp/example_tool.py'
        },
        metadata={
            'generated_at': '2025-12-02T10:00:00',
            'success_rate': 0.95,
            'frequency': 10,
            'category': 'example',
            'description': 'Example tool for demo'
        }
    )

    print(f"Publication result: {result['status']}")

    # Get registry stats
    stats = publisher.get_registry_stats()
    print(f"Total tools: {stats['total_tools']}")

asyncio.run(publish())
```

### 5. Run Full Orchestrator

```python
import asyncio
import sys
sys.path.append('/adapt/projects/firebird')

from agents.immortal.orchestrator import ImmortalOrchestrator

async def run_cycle():
    # Initialize orchestrator
    orchestrator = ImmortalOrchestrator(
        postgres_uri="postgresql://localhost:18030/firebird"
    )

    # Run single improvement cycle
    results = await orchestrator.run_single_cycle()

    print(f"\n{'═' * 79}")
    print("IMMORTAL CYCLE RESULTS")
    print(f"{'═' * 79}")

    print(f"Status: {results['overall_status']}")
    print(f"Started: {results['started_at']}")
    print(f"Completed: {results['completed_at']}")

    for phase, data in results['phases'].items():
        status = data.get('status', 'unknown')
        print(f"\n{phase.upper()}: {status}")

asyncio.run(run_cycle())
```

---

## 🔍 Debugging

### Check Database Tables

```bash
# Connect to PostgreSQL
psql -h localhost -p 18030 -U adapt firebird

# Show execution traces
\dt agent_executions
SELECT agent_type, status, COUNT(*) FROM agent_executions
GROUP BY agent_type, status;

# Show recent traces
SELECT * FROM agent_executions
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC
LIMIT 10;
```

### Check Vector Embeddings

```bash
# Connect to Qdrant
curl -X GET "http://localhost:18050/collections/tool_sequences" | jq

# Count vectors
curl -X POST "http://localhost:18050/collections/tool_sequences/points/count" \
  -H "Content-Type: application/json" \
  -d '{}' | jq
```

### Check Logs

```bash
# View orchestrator logs
tail -f agents/immortal/immortal.log

# View tool generation logs
tail -f agents/immortal/tool_synthesis/generation.log

# View pattern analysis logs
tail -f agents/immortal/learning_engine/analysis.log
```

### Test Individual Components

```python
# Test pattern detector
python -m agents.immortal.tool_synthesis.pattern_detector

# Test trace collector
python -m agents.immortal.learning_engine.trace_collector

# Test embedding generator
python -m agents.immortal.learning_engine.embedding_generator
```

---

## ⚡ Performance Tips

### 1. Reduce Analysis Frequency

Edit `orchestrator.py`:

```python
# Change from every 30 minutes to every 2 hours
await orchestrator.run_continuous(interval_minutes=120)
```

### 2. Increase Synthesis Threshold

Edit `tool_synthesis/pattern_detector.py`:

```python
# Only synthesize tools that appear 5+ times (not 3)
threshold_frequency = 5
```

### 3. Filter Low-Quality Data

Edit `learning_engine/trace_collector.py`:

```python
# Only collect completed executions (no failures)
SELECT * FROM agent_executions
WHERE status = 'completed' AND duration_seconds > 10
```

### 4. Batch Tool Generation

Generate tools in batches rather than one per cycle:

```python
# Generate up to 5 tools per cycle (not unlimited)
high_priority = synthesis_report['opportunities']['high_priority'][:5]
```

---

## 🎯 Common Patterns

### Pattern: "Search → Parse → Extract"

**When to expect synthesis:**
- Appears ≥ 3 times in 1 hour
- Success rate > 70%

**Generated tool name:** `search_parse_extract` or `extract_web_data`

**Use case:** Research agents pulling data from web sources

### Pattern: "Plan → Code → Test → Commit"

**When to expect synthesis:**
- Developer workflow repeated ≥ 5 times
- Code agent executions

**Generated tool name:** `develop_feature` or `implement_with_tests`

**Use case:** Code agents implementing features

### Pattern: "Read File → Edit → Save → Git Commit"

**When to expect synthesis:**
- File modification pattern repeated
- High success rate (> 80%)

**Generated tool name:** `edit_and_commit` or `modify_with_backup`

**Use case:** Safe file modifications with version control

---

## 📊 Monitoring Queries

### PostgreSQL

```sql
-- Success rate by agent type
SELECT
    agent_type,
    COUNT(*) as total,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successes,
    ROUND(
        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    ) as success_rate
FROM agent_executions
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY agent_type;

-- Average duration by tool sequence
SELECT
    tool_calls,
    AVG(duration_seconds) as avg_duration,
    COUNT(*) as frequency
FROM agent_executions
WHERE status = 'completed'
GROUP BY tool_calls
ORDER BY frequency DESC
LIMIT 10;
```

### Qdrant

```python
import requests

# Check collection status
collections = requests.get("http://localhost:18050/collections").json()
for col in collections['result']['collections']:
    print(f"{col['name']}: {col['vectors_count']} vectors")

# Find similar patterns
response = requests.post(
    "http://localhost:18050/collections/tool_sequences/points/search",
    json={
        "vector": [0.1, 0.2, ...],  # Your query vector
        "limit": 5
    }
)
```

---

## 🚨 Troubleshooting

### Problem: "No executions found"

**Solution:**
```bash
# Check if Temporal workflows are running
curl http://localhost:7233/api/v1/namespaces/default/workflows

# Check database connection
psql -h localhost -p 18030 -c "SELECT COUNT(*) FROM agent_executions"
```

### Problem: "Tool generation fails"

**Solution:**
```bash
# Check LLM API keys
source /adapt/secrets/m2.env
echo $MiniMax_M2_BASE_URL

# Test LLM connection
curl -H "Authorization: Bearer $MiniMax_M2_API_KEY" \
  $MiniMax_M2_BASE_URL/models
```

### Problem: "Embeddings not storing"

**Solution:**
```bash
# Check Qdrant is running
curl http://localhost:18050/health

# Check collection exists
curl http://localhost:18050/collections/tool_sequences

# Recreate collection if needed
```

### Problem: "Tests always fail"

**Solution:**
```bash
# Check test environment
python -m pytest --version

# Run simpler test
python -c "assert True, 'Test framework working'"

# Check file permissions
ls -la agents/immortal/tools/generated/
```

---

## 🎓 Next Steps

After mastering the basics:

1. **Customize thresholds** in `tool_synthesis/pattern_detector.py`
2. **Add new synthesis patterns** for your use cases
3. **Integrate with your agents** using the Tool Registry API
4. **Monitor with Grafana** dashboards (port 18031)
5. **Scale horizontally** with multiple orchestrator instances

---

## 📚 Full Documentation

See `README.md` for:
- Complete architecture
- Detailed component docs
- Evolution framework
- Safety & guardrails
- Success stories

See `ARCHITECTURE.md` for:
- Technical deep dives
- Data flow diagrams
- Integration patterns
- API specifications

---

## 🔗 Quick Links

- **Main Orchestrator**: `agents/immortal/orchestrator.py`
- **Learning Engine**: `agents/immortal/learning_engine/`
- **Tool Synthesis**: `agents/immortal/tool_synthesis/`
- **Tool Registry**: `core/tool_registry/`
- **Architecture**: `agents/immortal/ARCHITECTURE.md`

---

**🎯 Ready to build self-improving AI? Start with:**

```bash
cd /adapt/projects/firebird
python agents/immortal/orchestrator.py --mode single
```

**Happy building! 🚀**
