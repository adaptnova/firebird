"""Embedding Generator - Creates vector embeddings of patterns for semantic search."""

import logging
from typing import Dict, Any, List
import hashlib

from langchain_anthropic import ChatAnthropic
from langchain_core.embeddings import Embeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, Distance, VectorParams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleEmbeddingModel:
    """Simple sentence embedding using LLM. Replace with dedicated embedding model later."""

    def __init__(self):
        import os
        model_name = os.environ.get("MiniMax_M2_MODEL", "minimax-m2")
        base_url = os.environ.get("MiniMax_M2_BASE_URL", "https://api.minimax.io/anthropic")
        self.llm = ChatAnthropic(
            model=model_name,
            temperature=0,
            base_url=base_url
        )

    async def aembed_query(self, text: str) -> List[float]:
        """Generate embedding for a query."""
        # For MVP, use hash-based embeddings. Replace with real embeddings later.
        # This is a placeholder - in production, use a real embedding model
        import hashlib
        import struct

        # Simple hash-based embedding (deterministic but not semantic)
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()

        # Convert to 32 floats (256 bits / 8)
        embedding = []
        for i in range(0, min(256, len(hash_bytes)), 8):
            chunk = hash_bytes[i:i+8]
            if len(chunk) == 8:
                float_val = struct.unpack('d', chunk)[0]
                embedding.append(float_val)

        # Pad or truncate to exactly 32 dimensions
        while len(embedding) < 32:
            embedding.append(0.0)
        embedding = embedding[:32]

        return embedding

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple documents."""
        embeddings = []
        for text in texts:
            emb = await self.aembed_query(text)
            embeddings.append(emb)
        return embeddings


class EmbeddingGenerator:
    """Generates and manages vector embeddings of agent patterns."""

    def __init__(self, qdrant_url: str = "localhost:18050"):
        """Initialize embedding generator and Qdrant client."""
        self.qdrant_client = QdrantClient(qdrant_url)
        self.embeddings = SimpleEmbeddingModel()

        # Create collection if it doesn't exist
        self._setup_collections()

    def _setup_collections(self):
        """Setup Qdrant collections for different pattern types."""
        collections = ["tool_sequences", "success_patterns", "failure_patterns"]

        for collection_name in collections:
            try:
                self.qdrant_client.get_collection(collection_name)
                logger.info(f"Collection {collection_name} already exists")
            except Exception:
                # Collection doesn't exist, create it
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=32, distance=Distance.COSINE)
                )
                logger.info(f"Created collection: {collection_name}")

    async def store_tool_sequence(
        self,
        sequence: List[str],
        frequency: int,
        success_rate: float,
        avg_duration: float
    ) -> str:
        """Store a tool sequence pattern in vector DB."""
        pattern_text = f"Tool sequence: {' → '.join(sequence)}"

        # Create metadata-rich text for embedding
        embedding_text = f"""
        Tool sequence pattern: {' → '.join(sequence)}
        Frequency: {frequency}
        Success rate: {success_rate:.2f}
        Average duration: {avg_duration:.1f} seconds
        Recommendation: Consider creating a combined tool
        """

        # Generate embedding
        vector = await self.embeddings.aembed_query(embedding_text)

        # Generate unique ID
        import hashlib
        pattern_id = hashlib.md5(pattern_text.encode()).hexdigest()

        # Store in Qdrant
        self.qdrant_client.upsert(
            collection_name="tool_sequences",
            points=[PointStruct(
                id=pattern_id,
                vector=vector,
                payload={
                    "sequence": sequence,
                    "frequency": frequency,
                    "success_rate": success_rate,
                    "avg_duration": avg_duration,
                    "pattern_text": pattern_text,
                    "created_at": datetime.utcnow().isoformat()
                }
            )]
        )

        logger.info(f"Stored tool sequence pattern: {' → '.join(sequence)}")
        return pattern_id

    async def store_success_pattern(
        self,
        pattern: str,
        description: str,
        tasks_impacted: int,
        success_rate: float
    ) -> str:
        """Store a success pattern in vector DB."""
        embedding_text = f"""
        Success pattern: {pattern}
        Description: {description}
        Tasks impacted: {tasks_impacted}
        Success rate: {success_rate:.2f}
        Apply this pattern to similar tasks for better outcomes
        """

        vector = await self.embeddings.aembed_query(embedding_text)

        import hashlib
        pattern_id = hashlib.md5(pattern.encode()).hexdigest()

        self.qdrant_client.upsert(
            collection_name="success_patterns",
            points=[PointStruct(
                id=pattern_id,
                vector=vector,
                payload={
                    "pattern": pattern,
                    "description": description,
                    "tasks_impacted": tasks_impacted,
                    "success_rate": success_rate,
                    "pattern_text": pattern,
                    "created_at": datetime.utcnow().isoformat()
                }
            )]
        )

        logger.info(f"Stored success pattern: {pattern}")
        return pattern_id

    async def store_failure_pattern(
        self,
        pattern: str,
        root_cause: str,
        prevention_strategy: str,
        occurrence_rate: float
    ) -> str:
        """Store a failure pattern (anti-pattern) in vector DB."""
        embedding_text = f"""
        Failure pattern: {pattern}
        Root cause: {root_cause}
        Prevention strategy: {prevention_strategy}
        Occurrence rate: {occurrence_rate:.2f}
        Avoid this pattern to prevent failures
        """

        vector = await self.embeddings.aembed_query(embedding_text)

        import hashlib
        pattern_id = hashlib.md5(pattern.encode()).hexdigest()

        self.qdrant_client.upsert(
            collection_name="failure_patterns",
            points=[PointStruct(
                id=pattern_id,
                vector=vector,
                payload={
                    "pattern": pattern,
                    "root_cause": root_cause,
                    "prevention_strategy": prevention_strategy,
                    "occurrence_rate": occurrence_rate,
                    "pattern_text": pattern,
                    "created_at": datetime.utcnow().isoformat()
                }
            )]
        )

        logger.info(f"Stored failure pattern: {pattern}")
        return pattern_id

    async def search_similar_patterns(
        self,
        query: str,
        collection_name: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for patterns similar to a query."""
        vector = await self.embeddings.aembed_query(query)

        search_results = self.qdrant_client.search(
            collection_name=collection_name,
            query_vector=vector,
            limit=limit
        )

        patterns = []
        for result in search_results:
            patterns.append({
                "id": result.id,
                "score": result.score,
                "payload": result.payload
            })

        logger.info(f"Found {len(patterns)} similar patterns in {collection_name}")
        return patterns

    async def find_relevant_patterns(
        self,
        current_task: str,
        pattern_type: str = "success_patterns"
    ) -> List[Dict[str, Any]]:
        """Find relevant patterns for a given task."""
        patterns = await self.search_similar_patterns(
            current_task,
            collection_name=pattern_type,
            limit=3
        )

        return patterns

    async def get_recent_patterns(
        self,
        collection_name: str,
        hours: int = 24,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recently added patterns."""
        # For MVP, just search with a generic query to get recent items
        # In production, use timestamp filtering
        patterns = await self.search_similar_patterns(
            "recent patterns",
            collection_name=collection_name,
            limit=limit
        )

        return patterns


# Example usage
async def main():
    """Demo embedding generation."""
    generator = EmbeddingGenerator()

    # Store some example patterns
    await generator.store_tool_sequence(
        sequence=["search_web", "parse_html", "extract_data"],
        frequency=8,
        success_rate=0.9,
        avg_duration=45.5
    )

    # Search for similar patterns
    patterns = await generator.search_similar_patterns(
        "web search and data extraction",
        collection_name="tool_sequences"
    )

    print(f"Found {len(patterns)} matching patterns")
    for pattern in patterns:
        print(f"- Score: {pattern['score']:.3f}")
        print(f"  Sequence: {' → '.join(pattern['payload']['sequence'])}")
        print(f"  Frequency: {pattern['payload']['frequency']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
