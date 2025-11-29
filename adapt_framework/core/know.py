"""
KNOW - Self and others

Core knowledge module for self-awareness, team awareness, tool knowledge, and context understanding.
Implements the 'KNOW' principle from PACK-I.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
import inspect


@dataclass
class SelfKnowledge:
    """Knowledge about the agent itself."""

    capabilities: List[str]
    limitations: List[str]
    preferences: Dict[str, Any]
    performance_history: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ToolKnowledge:
    """Knowledge about a tool."""

    name: str
    description: str
    category: str
    usage_count: int
    success_rate: float
    avg_execution_time: float
    last_used: Optional[str]
    parameters: List[str]
    returns: str
    examples: List[str]


@dataclass
class TeamKnowledge:
    """Knowledge about team members."""

    name: str
    role: str
    capabilities: List[str]
    responsibilities: List[str]
    collaboration_history: List[Dict[str, Any]]
    strengths: List[str]
    weaknesses: List[str]


class KnowledgeManager:
    """
    Manages knowledge about self, tools, team, and context.
    Enables the ADAPT framework to "know" what it's capable of.
    """

    def __init__(self, knowledge_file: Optional[str] = None):
        """
        Initialize knowledge manager.

        Args:
            knowledge_file: Path to knowledge store. Defaults to ~/.adapt_knowledge/
        """
        if knowledge_file is None:
            knowledge_file = str(Path.home() / ".adapt_knowledge" / "knowledge.json")

        self.knowledge_file = Path(knowledge_file)
        self.knowledge_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize if doesn't exist
        if not self.knowledge_file.exists():
            self._initialize_default_knowledge()

        self.knowledge = self._load_knowledge()

    def _initialize_default_knowledge(self):
        """Initialize with default self-knowledge."""
        default_knowledge = {
            "self": {
                "capabilities": [
                    "Analyze and understand tasks",
                    "Create detailed implementation plans",
                    "Write code in multiple languages",
                    "Use external tools and APIs",
                    "Learn from past experiences",
                    "Collaborate with other agents",
                    "Debug and troubleshoot issues",
                    "Review and improve code"
                ],
                "limitations": [
                    "Cannot access external systems not configured",
                    "Limited by API rate limits",
                    "May occasionally make assumptions",
                    "Cannot execute code that requires interaction",
                    "Cannot access internet without tools"
                ],
                "preferences": {
                    "code_style": "Clean, documented, and tested",
                    "communication": "Direct and efficient",
                    "error_handling": "Graceful with clear messages",
                    "planning": "Detailed with milestones"
                },
                "performance_history": []
            },
            "tools": {},
            "team": {},
            "context": {}
        }

        self._save_knowledge(default_knowledge)

    def _load_knowledge(self) -> Dict[str, Any]:
        """Load knowledge from file."""
        try:
            return json.loads(self.knowledge_file.read_text())
        except Exception as e:
            print(f"Error loading knowledge: {e}")
            self._initialize_default_knowledge()
            return json.loads(self.knowledge_file.read_text())

    def _save_knowledge(self, knowledge: Optional[Dict[str, Any]] = None):
        """Save knowledge to file."""
        if knowledge is None:
            knowledge = self.knowledge

        self.knowledge_file.write_text(json.dumps(knowledge, indent=2))

    # Self Knowledge

    def update_self_capability(self, capability: str, add: bool = True):
        """Add or remove a capability."""
        if add:
            if capability not in self.knowledge["self"]["capabilities"]:
                self.knowledge["self"]["capabilities"].append(capability)
        else:
            if capability in self.knowledge["self"]["capabilities"]:
                self.knowledge["self"]["capabilities"].remove(capability)

        self._save_knowledge()

    def update_self_limitation(self, limitation: str, add: bool = True):
        """Add or remove a limitation."""
        if add:
            if limitation not in self.knowledge["self"]["limitations"]:
                self.knowledge["self"]["limitations"].append(limitation)
        else:
            if limitation in self.knowledge["self"]["limitations"]:
                self.knowledge["self"]["limitations"].remove(limitation)

        self._save_knowledge()

    def set_preference(self, category: str, value: Any):
        """Set a preference."""
        self.knowledge["self"]["preferences"][category] = value
        self._save_knowledge()

    def get_preference(self, category: str, default: Any = None) -> Any:
        """Get a preference."""
        return self.knowledge["self"]["preferences"].get(category, default)

    def record_performance(self, metrics: Dict[str, Any]):
        """Record performance metrics."""
        self.knowledge["self"]["performance_history"].append({
            "timestamp": datetime.now().isoformat(),
            **metrics
        })

        # Keep only last 1000 entries to prevent bloat
        if len(self.knowledge["self"]["performance_history"]) > 1000:
            self.knowledge["self"]["performance_history"] = \
                self.knowledge["self"]["performance_history"][-1000:]

        self._save_knowledge()

    def get_average_performance(self, metric: str) -> float:
        """Get average performance for a specific metric."""
        history = self.knowledge["self"]["performance_history"]

        if not history:
            return 0.0

        values = [h.get(metric, 0) for h in history if metric in h]
        if not values:
            return 0.0

        return sum(values) / len(values)

    # Tool Knowledge

    def register_tool(self, tool_name: str, tool_info: Dict[str, Any]):
        """
        Register a tool in the knowledge base.

        Args:
            tool_name: Name of the tool
            tool_info: Tool information (description, params, etc.)
        """
        if tool_name not in self.knowledge["tools"]:
            self.knowledge["tools"][tool_name] = {
                "name": tool_name,
                "description": tool_info.get("description", ""),
                "category": tool_info.get("category", "general"),
                "usage_count": 0,
                "success_rate": 1.0,
                "total_calls": 0,
                "successful_calls": 0,
                "avg_execution_time": 0.0,
                "last_used": None,
                "parameters": tool_info.get("parameters", []),
                "returns": tool_info.get("returns", ""),
                "examples": tool_info.get("examples", [])
            }

            self._save_knowledge()

    def update_tool_stats(
        self,
        tool_name: str,
        success: bool,
        execution_time: float
    ):
        """Update tool statistics after usage."""
        if tool_name not in self.knowledge["tools"]:
            return

        tool = self.knowledge["tools"][tool_name]
        tool["total_calls"] += 1
        tool["last_used"] = datetime.now().isoformat()

        if success:
            tool["successful_calls"] += 1

        tool["success_rate"] = tool["successful_calls"] / tool["total_calls"]

        # Update average execution time
        old_avg = tool["avg_execution_time"]
        n = tool["total_calls"]
        tool["avg_execution_time"] = ((old_avg * (n - 1)) + execution_time) / n

        self._save_knowledge()

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a tool."""
        return self.knowledge["tools"].get(tool_name)

    def list_tools_by_category(self, category: str) -> List[str]:
        """List all tools in a category."""
        return [
            name for name, info in self.knowledge["tools"].items()
            if info.get("category") == category
        ]

    def get_best_tools(self, limit: int = 5) -> List[str]:
        """Get the best performing tools by success rate and usage."""
        tools = []
        for name, info in self.knowledge["tools"].items():
            if info["total_calls"] > 0:
                score = info["success_rate"] * min(info["total_calls"] / 10, 1.0)
                tools.append((name, score))

        tools.sort(key=lambda x: x[1], reverse=True)
        return [t[0] for t in tools[:limit]]

    # Team Knowledge

    def register_team_member(self, name: str, role: str, capabilities: List[str]):
        """Register a team member."""
        self.knowledge["team"][name] = {
            "name": name,
            "role": role,
            "capabilities": capabilities,
            "responsibilities": [],
            "collaboration_history": [],
            "strengths": [],
            "weaknesses": []
        }

        self._save_knowledge()

    def update_team_member(self, name: str, updates: Dict[str, Any]):
        """Update team member information."""
        if name in self.knowledge["team"]:
            self.knowledge["team"][name].update(updates)
            self._save_knowledge()

    def record_collaboration(self, teammate_name: str, task: str, outcome: str, success: bool):
        """Record collaboration with a teammate."""
        if teammate_name not in self.knowledge["team"]:
            return

        collaboration = {
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "outcome": outcome,
            "success": success
        }

        self.knowledge["team"][teammate_name]["collaboration_history"].append(collaboration)
        self._save_knowledge()

    def get_team_member(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a team member."""
        return self.knowledge["team"].get(name)

    def get_team_by_capability(self, capability: str) -> List[str]:
        """Get team members with a specific capability."""
        return [
            name for name, info in self.knowledge["team"].items()
            if capability in info.get("capabilities", [])
        ]

    # Context

    def set_context(self, key: str, value: Any):
        """Set contextual information."""
        self.knowledge["context"][key] = value
        self._save_knowledge()

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get contextual information."""
        return self.knowledge["context"].get(key, default)

    def clear_context(self):
        """Clear context."""
        self.knowledge["context"].clear()
        self._save_knowledge()

    # Self-Assessment

    def self_assessment(self) -> Dict[str, Any]:
        """Generate a self-assessment."""
        self_knowledge = self.knowledge["self"]

        # Analyze performance history
        history = self_knowledge["performance_history"]

        if len(history) >= 10:
            recent = history[-10:]
            successes = sum(1 for h in recent if h.get("success", False))
            success_rate = successes / len(recent)
        else:
            success_rate = None

        # Get best tools
        best_tools = self.get_best_tools(3)

        # Get team strengths
        team_strengths = {}
        for name, info in self.knowledge["team"].items():
            team_strengths[name] = info.get("strengths", [])

        return {
            "capabilities": len(self_knowledge["capabilities"]),
            "limitations": len(self_knowledge["limitations"]),
            "success_rate": success_rate,
            "best_tools": best_tools,
            "team_members": len(self.knowledge["team"]),
            "team_strengths": team_strengths,
            "total_memories": self.get_total_memory_count(),
        }

    def get_total_memory_count(self) -> int:
        """Get total number of memories across all categories."""
        # This would integrate with the PersistentMemory class
        return 0  # Placeholder
