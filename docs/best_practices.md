# 🎯 FIREBIRD BEST PRACTICES
## Development & Operational Guidelines

---

## 🎨 AGENT DEVELOPMENT

### 1. Type Safety First
```python
# ✅ GOOD: Use Pydantic models
class ResearchReport(BaseModel):
    title: str
    summary: str
    sources: List[str]
    confidence: float = Field(ge=0, le=1)

# ❌ BAD: No type validation
def research():
    return {"title": "..."}  # Unvalidated
```

### 2. Temporal for Durability
```python
# ✅ GOOD: Every agent uses Temporal
@workflow.defn
class ResearchWorkflow:
    @workflow.run
    async def run(self, topic: str):
        # Crash-proof execution
        result = await workflow.execute_activity(search_activity, topic)
        return result

# ❌ BAD: No durability
async def research(topic):
    return await search(topic)  # Lost on crash
```

### 3. Async Everything
```python
# ✅ GOOD: Parallel execution
async def parallel_search(queries: List[str]):
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(search(q)) for q in queries]
    return [task.result() for task in tasks]

# ❌ BAD: Sequential (slow)
for query in queries:
    results.append(await search(query))
```

### 4. Self-Documenting
```python
# ✅ GOOD: Docstrings everywhere
async def research_agent(topic: str) -> ResearchReport:
    """Conducts autonomous research on a given topic.
    
    Args:
        topic: The research topic to investigate
        
    Returns:
        ResearchReport with title, summary, sources, confidence
        
    Raises:
        ResearchError: If research fails after 3 retries
    """
    pass

# ❌ BAD: No documentation
def research(x):
    pass
```

---

## 🗄️ DATABASE USAGE

### PostgreSQL + TimescaleDB
```python
# ✅ GOOD: Use for time-series and structured data
CREATE TABLE agent_metrics (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metric_name VARCHAR(100),
    metric_value FLOAT
);

# Query recent metrics
SELECT * FROM agent_metrics 
WHERE timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;
```

### Qdrant (Vector DB)
```python
# ✅ GOOD: Use for embeddings, semantic search
qdrant_client.create_collection(
    collection_name="agent_memory",
    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
)

# Store embeddings
qdrant_client.upsert(
    collection_name="agent_memory",
    points=[PointStruct(id=1, vector=embedding, payload={"text": text})]
)

# Semantic search
results = qdrant_client.search(
    collection_name="agent_memory",
    query_vector=query_embedding,
    limit=5
)
```

### MongoDB
```python
# ✅ GOOD: Use for documents, unstructured data
db.reports.insert_one({
    "title": "Market Analysis",
    "content": "...",
    "created_at": datetime.utcnow(),
    "agent_id": "analysis-v1"
})

# Query documents
report = db.reports.find_one({"title": "Market Analysis"})
```

### Neo4j (Graph)
```python
# ✅ GOOD: Use for relationships, knowledge graphs
graph.create(
    Node("Research", topic="AI"),
    Node("Research", topic="ML"),
    Relationship(
        start_node=research_ai,
        end_node=research_ml,
        rel_type="RELATES_TO"
    )
)
```

### ClickHouse (Analytics)
```python
# ✅ GOOD: Use for real-time analytics
INSERT INTO agent_metrics (agent_id, metric_name, value)
VALUES ('research-v1', 'tasks_completed', 1)

# Aggregate queries
SELECT 
    agent_id,
    count() as tasks_count,
    avg(value) as avg_value
FROM agent_metrics
GROUP BY agent_id
```

### QuestDB (High-Freq Time-Series)
```python
# ✅ GOOD: Use for metrics, monitoring
questdb.query(f"""
    INSERT INTO agent_metrics 
    (timestamp, agent_id, metric_name, value)
    VALUES ({now_ms()}, 'research-v1', 'latency_ms', {latency})
""")
```

---

## 📨 MESSAGE BUS PATTERNS

### RedPanda (Kafka) - High Throughput
```python
# ✅ GOOD: Use for event streaming
producer = KafkaProducer(
    bootstrap_servers=['localhost:18020'],
    value_serializer=lambda v: json.dumps(v).encode()
)

# Publish event
producer.send('firebird.research.request', {
    'topic': 'quantum computing',
    'timestamp': time.time()
})

# Consumer
consumer = KafkaConsumer(
    'firebird.research.request',
    bootstrap_servers=['localhost:18020'],
    value_deserializer=lambda m: json.loads(m.decode())
)
```

### Pulsar (Pub/Sub) - Flexible
```python
# ✅ GOOD: Use for pub/sub
client = pulsar.Client('pulsar://localhost:8080')
producer = client.create_producer('firebird/analysis')

producer.send(json.dumps({'data': '...'}).encode('utf-8'))

consumer = client.subscribe(
    'firebird/analysis',
    subscription_name='my-sub'
)
```

### NATS - Lightweight
```python
# ✅ GOOD: Use for agent-to-agent
nc = NATS()

await nc.connect(servers=["nats://localhost:18020"])

# Publish
await nc.publish("agents.research", b"Hello Research Agent!")

# Subscribe
async def handler(msg):
    print(f"Received: {msg.data}")

await nc.subscribe("agents.*", cb=handler)
```

---

## 🤖 LLM INTEGRATION

### Smart Routing
```python
# ✅ GOOD: Route to best model
async def complete_with_best_model(task_type, prompt):
    if task_type == "coding":
        return await groq.complete("llama-3.3-70b-versatile", prompt)
    elif task_type == "reasoning":
        return await moonshot.complete("kimi-k2-thinking", prompt)
    elif task_type == "fast":
        return await groq.complete("llama-3.1-8b-instant", prompt)
    else:
        return await groq.complete("llama-3.3-70b-versatile", prompt)
```

### Failover Strategy
```python
# ✅ GOOD: Multiple providers
async def complete_with_failover(prompt):
    providers = [groq, moonshot, huggingface]
    for provider in providers:
        try:
            return await provider.complete(prompt)
        except Exception as e:
            logger.warning(f"Provider failed: {e}")
            continue
    raise Exception("All providers failed")
```

---

## 🔍 SEARCH INTEGRATION

### Parallel Search
```python
# ✅ GOOD: Use all APIs in parallel
async def search_all(query):
    tasks = [
        tavily_search(query),
        brave_search(query),
        perplexity_search(query),
        serper_search(query),
        jina_search(query),
        firecrawl_search(query),
        algolia_search(query),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return merge_and_deduplicate(results)
```

### Result Merging
```python
# ✅ GOOD: Deduplicate and rank
def merge_results(results_list):
    all_results = []
    for results in results_list:
        if isinstance(results, Exception):
            continue
        all_results.extend(results)
    
    # Deduplicate by URL
    seen_urls = set()
    unique_results = []
    for result in all_results:
        if result['url'] not in seen_urls:
            seen_urls.add(result['url'])
            unique_results.append(result)
    
    # Rank by relevance score
    return sorted(unique_results, key=lambda x: x['score'], reverse=True)
```

---

## 📊 MONITORING & OBSERVABILITY

### Metrics Collection
```python
# ✅ GOOD: Collect metrics
from prometheus_client import Counter, Histogram, Gauge

tasks_completed = Counter('agent_tasks_completed', 'Tasks completed', ['agent'])
task_duration = Histogram('agent_task_duration_seconds', 'Task duration', ['agent'])
active_agents = Gauge('agent_active_count', 'Number of active agents')

# Use metrics
def track_task(agent):
    start = time.time()
    try:
        result = agent.execute()
        tasks_completed.labels(agent=agent.name).inc()
        return result
    finally:
        duration = time.time() - start
        task_duration.labels(agent=agent.name).observe(duration)
```

### Health Checks
```python
# ✅ GOOD: Health check every agent
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "checks": {
            "database": await check_database(),
            "message_bus": await check_message_bus(),
            "apis": await check_apis(),
        }
    }
```

---

## 🔒 SECURITY

### API Key Management
```python
# ✅ GOOD: Use environment variables
import os
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not set")

# ❌ BAD: Hardcoded keys
GROQ_API_KEY = "gsk_1234567890"  # Never!
```

### Input Validation
```python
# ✅ GOOD: Validate all inputs
from pydantic import BaseModel, Field, ValidationError

class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    max_results: int = Field(default=10, ge=1, le=100)
    safe_search: bool = True

# Validate
try:
    request = SearchRequest(query="AI trends", max_results=5)
except ValidationError as e:
    return {"error": str(e)}
```

### Rate Limiting
```python
# ✅ GOOD: Rate limit API calls
from asyncio import Semaphore

semaphore = Semaphore(10)  # Max 10 concurrent calls

async def limited_call(func, *args):
    async with semaphore:
        return await func(*args)
```

---

## 🧪 TESTING

### Unit Tests
```python
# ✅ GOOD: Test everything
import pytest
from agents.research import ResearchAgent

@pytest.mark.asyncio
async def test_research_agent():
    agent = ResearchAgent()
    result = await agent.research("quantum computing")
    assert isinstance(result, ResearchReport)
    assert len(result.sources) > 0
    assert 0 <= result.confidence <= 1
```

### Integration Tests
```python
# ✅ GOOD: Test with real services
@pytest.mark.integration
async def test_database_connection():
    client = PostgreSQLClient()
    await client.connect()
    result = await client.query("SELECT 1")
    assert result == 1
    await client.disconnect()
```

---

## 📝 DOCUMENTATION

### Code Comments
```python
# ✅ GOOD: Explain why, not what
async def parallel_search(queries):
    # Use asyncio.TaskGroup for bounded parallelism
    # instead of asyncio.gather to get early cancellation
    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(search(q)) 
            for q in queries
        ]
    return [task.result() for task in tasks]

# ❌ BAD: Redundant comments
async def parallel_search(queries):
    # Create tasks
    for query in queries:
        await search(query)  # Search for query
```

### Docstrings
```python
# ✅ GOOD: Comprehensive docstrings
async def analyze_research(report: ResearchReport) -> Analysis:
    """Analyzes research report and generates insights.
    
    Performs pattern recognition, trend identification, and
    risk assessment on the research report.
    
    Args:
        report: The research report to analyze
        
    Returns:
        Analysis object containing insights, patterns, and recommendations
        
    Raises:
        AnalysisError: If analysis fails after maximum retries
        
    Example:
        report = await research_agent.research("AI trends")
        analysis = await analyze_research(report)
        print(analysis.insights)
    """
    pass
```

---

## 🚀 DEPLOYMENT

### Environment-Specific Configs
```python
# ✅ GOOD: Different configs for dev/staging/prod
# config/development.yaml
database:
  host: localhost
  port: 18030
  
# config/production.yaml  
database:
  host: db.prod.firebird.ai
  port: 5432
  ssl: true
```

### Container Best Practices
```dockerfile
# ✅ GOOD: Multi-stage build, non-root user
FROM python:3.12-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
USER 1000
CMD ["python", "-m", "agents.research"]
```

---

## 📊 PERFORMANCE

### Caching
```python
# ✅ GOOD: Cache expensive operations
from functools import lru_cache
import redis

redis_client = redis.Redis(host='localhost', port=18000)

async def get_embeddings(text):
    cache_key = f"embed:{hash(text)}"
    cached = await redis_client.get(cache_key)
    if cached:
        return pickle.loads(cached)
    
    embedding = await generate_embedding(text)
    await redis_client.setex(
        cache_key, 
        3600,  # 1 hour
        pickle.dumps(embedding)
    )
    return embedding
```

### Connection Pooling
```python
# ✅ GOOD: Reuse connections
import asyncpg

class DatabasePool:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        self.pool = await asyncpg.create_pool(
            "postgresql://localhost:18030",
            min_size=5,
            max_size=20
        )
    
    async def query(self, sql):
        async with self.pool.acquire() as conn:
            return await conn.fetch(sql)
```

---

## 🔄 CONTINUOUS IMPROVEMENT

### Learning Loops
```python
# ✅ GOOD: Learn from feedback
async def improve_agent(agent, feedback):
    # Store feedback in database
    await db.feedback.insert_one({
        "agent_id": agent.id,
        "feedback": feedback,
        "timestamp": datetime.utcnow()
    })
    
    # Periodic model retraining
    await retrain_if_needed(agent)
```

### A/B Testing
```python
# ✅ GOOD: Test improvements
async def get_best_model(task_type):
    # 90% use current best, 10% test new
    if random.random() < 0.1:
        return await test_new_model(task_type)
    else:
        return await get_production_model(task_type)
```

---

## 📋 CHECKLIST

### Before Committing Code
- [ ] All tests passing
- [ ] Type hints added
- [ ] Docstrings complete
- [ ] No hardcoded secrets
- [ ] Logging added
- [ ] Metrics collected
- [ ] Documentation updated

### Before Deploying
- [ ] Integration tests pass
- [ ] Load testing complete
- [ ] Rollback plan ready
- [ ] Monitoring dashboards updated
- [ ] Alert rules configured
- [ ] Team notified

---

## 🎯 KEY PRINCIPLES

1. **Type Safety**: Everything typed with Pydantic
2. **Durability**: Every workflow uses Temporal
3. **Parallelism**: Async/await everywhere
4. **Observability**: Metrics + logging + tracing
5. **Self-Documenting**: Docstrings + architecture docs
6. **Testable**: 100% test coverage
7. **Secure**: No secrets, input validation
8. **Performant**: Caching + connection pooling
9. **Resilient**: Retries + circuit breakers
10. **Learnable**: Feedback loops + A/B testing

---

**Status**: ✅ Best practices documented
**Next**: Start implementation (Phase 1!)
