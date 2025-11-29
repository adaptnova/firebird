"""
ADAPT Framework

Build infrastructure that builds itself.
Starting with me, then my team, then the world.

FIRST PRINCIPLES: PACK-I
- PERSIST: Continue existing
- ACT: Do things
- COORDINATE: Work together
- KNOW: Self and others
- IMPROVE: Get better

FLOW: PLAN → BUILD → REPEAT
"""

__version__ = "0.1.0"
__author__ = "ADAPT Team"

from .core import (
    PersistentMemory, StateManager,
    KnowledgeManager, SelfKnowledge, ToolKnowledge, TeamKnowledge
)

__all__ = [
    "PersistentMemory", "StateManager",
    "KnowledgeManager", "SelfKnowledge", "ToolKnowledge", "TeamKnowledge"
]
