"""
ADAPT Framework Core Modules

Implements the PACK-I principles:
- PERSIST: Continue existing
- ACT: Do things
- COORDINATE: Work together
- KNOW: Self and others
- IMPROVE: Get better
"""

from .persist import PersistentMemory, StateManager
from .know import KnowledgeManager, SelfKnowledge, ToolKnowledge, TeamKnowledge

__all__ = [
    "PersistentMemory", "StateManager",
    "KnowledgeManager", "SelfKnowledge", "ToolKnowledge", "TeamKnowledge"
]
