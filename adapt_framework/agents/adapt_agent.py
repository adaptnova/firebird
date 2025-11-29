"""
ADAPT Agent

Main agent class that integrates all ADAPT framework modules:
- PERSIST: Memory and state management
- KNOW: Knowledge of self/tools/team
- ACT: Action execution
- COORDINATE: Multi-agent collaboration
- IMPROVE: Self-improvement (future)

Implements the ADAPT flow: PLAN → BUILD → REPEAT
"""

import asyncio
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from ..core.persist import PersistentMemory, StateManager
from ..core.know import KnowledgeManager
from ..core.act import ToolRegistry, ActionExecutor, ActionPlanner, ActionResult
from ..core.coordinate import TeamCoordinator, Task


class ADAPTAgent:
    """
    Main ADAPT agent that can plan, act, learn, and coordinate.

    Integrates all PACK-I principles into a cohesive agent architecture.
    """

    def __init__(
        self,
        name: str,
        capabilities: Optional[List[str]] = None,
        memory_path: Optional[str] = None,
        knowledge_path: Optional[str] = None
    ):
        """
        Initialize ADAPT agent.

        Args:
            name: Agent name
            capabilities: List of agent capabilities
            memory_path: Path for memory storage
            knowledge_path: Path for knowledge storage
        """
        self.name = name
        self.capabilities = capabilities or []

        # Initialize core modules
        self.memory = PersistentMemory(storage_path=memory_path)
        self.knowledge = KnowledgeManager(knowledge_file=knowledge_path)
        self.registry = ToolRegistry()
        self.executor = ActionExecutor(registry=self.registry, knowledge_manager=self.knowledge)
        self.planner = ActionPlanner(registry=self.registry, knowledge_manager=self.knowledge)
        self.coordinator = None  # Set when part of a team

        # State management
        self.session_id = None
        self.state = None

        # Register self in knowledge
        self._initialize_self_knowledge()

        print(f"🤖 ADAPT Agent '{name}' initialized")
        print(f"   Capabilities: {', '.join(self.capabilities)}")
        print(f"   Memory: {self.memory.storage_path}")
        print(f"   Knowledge: {self.knowledge.knowledge_file}")

    def _initialize_self_knowledge(self):
        """Initialize self-knowledge in the knowledge base."""
        # Set basic capabilities
        for capability in self.capabilities:
            self.knowledge.update_self_capability(capability, add=True)

        # Set preferences
        self.knowledge.set_preference("communication_style", "direct_and_efficient")
        self.knowledge.set_preference("planning_style", "detailed_with_milestones")
        self.knowledge.set_preference("error_handling", "graceful_with_retries")

    def start_session(self, session_name: str, metadata: Optional[Dict] = None) -> str:
        """
        Start a new session for this agent.

        Args:
            session_name: Session name/ID
            metadata: Optional session metadata

        Returns:
            Session ID
        """
        self.session_id = self.memory.create_session(session_name, metadata)
        self.state = StateManager(self.session_id, self.memory)

        # Store session info in agent state
        self.state.set("session_name", session_name)
        self.state.set("agent_name", self.name)
        self.state.set("start_time", self._get_timestamp())

        print(f"📋 Session '{session_name}' started (ID: {self.session_id[:8]})")
        return self.session_id

    def register_tool(self, name: str, func: callable, info: Optional[Dict] = None):
        """
        Register a tool with the agent.

        Args:
            name: Tool name
            func: Tool function
            info: Optional tool metadata
        """
        self.registry.register(name, func, info)

        # Also register in knowledge
        if info is None:
            info = self.registry.get_info(name)

        self.knowledge.register_tool(name, info or {})
        print(f"🔧 Tool '{name}' registered")

    def register_tools_from_module(self, module):
        """
        Register all tools from a module.
        Looks for functions that start with 'tool_' or have appropriate decorators.

        Args:
            module: Module to scan for tools
        """
        import inspect

        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) and not name.startswith("_"):
                # Register all public functions as tools
                self.register_tool(name, obj)

    def run(self, task: str, mode: str = "plan_build") -> Dict[str, Any]:
        """
        Run the agent on a task.

        Args:
            task: Task description
            mode: Execution mode ('plan_build', 'direct', 'research')

        Returns:
            Task results and metadata
        """
        if self.session_id is None:
            self.start_session(f"task_{self.name}_{self._get_timestamp()}")

        print(f"\n{'='*60}")
        print(f"🎯 TASK: {task}")
        print(f"🤖 AGENT: {self.name}")
        print(f"{'='*60}")

        # Record event
        self.memory.record_event(
            self.session_id,
            "task_start",
            f"agent_{self.name}_run",
            metadata={"task": task, "mode": mode}
        )

        # PERSIST: Load relevant memories
        relevant_memories = self.memory.recall_memory(
            self.session_id,
            memory_type="learning",
            limit=5
        )

        if relevant_memories:
            print(f"📚 Loaded {len(relevant_memories)} relevant memories")

        # KNOW: Get context about self and tools
        self_knowledge = self.knowledge.self_assessment()
        best_tools = self.knowledge.get_best_tools(3)

        print(f"💡 Best tools available: {', '.join(best_tools)}")

        # ACT: Execute based on mode
        start_time = self._get_timestamp()

        if mode == "plan_build":
            result = self._plan_build_execute(task)
        elif mode == "direct":
            result = self._direct_execute(task)
        elif mode == "research":
            result = self._research_execute(task)
        else:
            result = {"error": f"Unknown mode: {mode}"}

        end_time = self._get_timestamp()

        # Save result to memory
        self.memory.save_memory(
            self.session_id,
            "task_result",
            {
                "task": task,
                "mode": mode,
                "result": result,
                "start_time": start_time,
                "end_time": end_time
            },
            importance=0.8
        )

        # Record completion
        self.memory.record_event(
            self.session_id,
            "task_complete",
            f"agent_{self.name}_run",
            outcome="success" if "error" not in result else "failed",
            success="error" not in result,
            metadata=result
        )

        # Print summary
        print(f"\n{'='*60}")
        print(f"✅ TASK COMPLETE")
        print(f"⏱️  Duration: {end_time - start_time:.2f}s")
        print(f"{'='*60}\n")

        return result

    def _plan_build_execute(self, task: str) -> Dict[str, Any]:
        """Execute using PLAN → BUILD flow."""
        print(f"\n📋 PLANNING...")

        # Create plan
        plan = self.planner.create_plan(task)
        print(f"✅ Plan created: {plan.description}")
        print(f"   Estimated time: {plan.estimated_time}s")
        print(f"   Actions: {len(plan.actions)}")

        # Validate plan
        is_valid, issues = self.planner.validate_plan(plan)
        if not is_valid:
            print(f"❌ Plan validation failed: {issues}")
            return {"error": "Plan validation failed", "issues": issues}

        # BUILD: Execute plan
        print(f"\n🔨 BUILDING...")
        results = self.executor.execute_batch(plan.actions, continue_on_error=False)

        # Analyze results
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        print(f"✅ Completed: {successful}/{len(results)} actions")
        if failed > 0:
            print(f"❌ Failed: {failed} actions")

        return {
            "mode": "plan_build",
            "plan": plan.to_dict(),
            "results": [r.to_dict() for r in results],
            "successful_actions": successful,
            "total_actions": len(results)
        }

    def _direct_execute(self, task: str) -> Dict[str, Any]:
        """Execute task directly with minimal planning."""
        print(f"\n⚡ DIRECT EXECUTION...")

        # Simple heuristic: if task mentions a tool, use it
        tool_scores = {}
        for tool_name in self.registry.list_tools():
            if tool_name.lower() in task.lower():
                tool_scores[tool_name] = 1.0

        # Use best scoring tool, or default to research
        if tool_scores:
            best_tool = max(tool_scores.keys(), key=lambda k: tool_scores[k])
            action = {"tool": best_tool, "params": {"query": task}}
        else:
            action = {"tool": "file_read", "params": {"path": "/data/example.txt"}}

        result = self.executor.execute(action["tool"], action.get("params", {}))

        return {
            "mode": "direct",
            "action": action,
            "result": result.to_dict() if hasattr(result, 'to_dict') else str(result)
        }

    def _research_execute(self, task: str) -> Dict[str, Any]:
        """Execute in research mode - gather information and analyze."""
        print(f"\n🔍 RESEARCH MODE...")

        # Research actions
        research_actions = []
        if "file" in task.lower():
            research_actions.append({"tool": "file_read", "params": {"path": "/data"}})

        # Add analysis
        research_actions.append({"tool": "file_read", "params": {"path": "/data/example.txt"}})

        results = self.executor.execute_batch(research_actions, continue_on_error=True)

        successful = [r for r in results if r.success]

        return {
            "mode": "research",
            "results": [r.to_dict() for r in successful],
            "summary": f"Gathered {len(successful)} pieces of information"
        }

    def learn_from_result(self, result: Dict[str, Any]):
        """
        Learn from task execution result.

        Args:
            result: Task execution result
        """
        # Extract learnings
        learnings = []

        if result.get("successful_actions") == result.get("total_actions"):
            learnings.append("All actions succeeded - this approach works well")

        # Save learnings
        for learning in learnings:
            self.memory.save_memory(
                self.session_id,
                "learning",
                learning,
                importance=0.7
            )

        # Update knowledge based on results
        self.knowledge.record_performance(result)

    def add_to_team(self, coordinator: TeamCoordinator):
        """
        Add this agent to a team coordinator.

        Args:
            coordinator: Team coordinator instance
        """
        self.coordinator = coordinator
        coordinator.register_agent(self.name, self, self.capabilities)
        print(f"👥 Agent '{self.name}' added to team")

    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        # Get knowledge dictionary - try method first, fall back to attribute
        knowledge_dict = {}
        if hasattr(self.knowledge, 'knowledge'):
            knowledge_dict = self.knowledge.knowledge
        knowledge_size = sum(len(v) for v in knowledge_dict.values()) if isinstance(knowledge_dict, dict) else 0

        return {
            "name": self.name,
            "session_id": self.session_id,
            "capabilities": self.capabilities,
            "memory_count": self.memory.get_session_stats(self.session_id).get("memory_count", 0) if self.session_id else 0,
            "knowledge_size": knowledge_size,
            "registered_tools": len(self.registry.list_tools()),
            "in_team": self.coordinator is not None
        }

    def print_status(self):
        """Print agent status summary."""
        status = self.get_status()

        print(f"\n{'='*60}")
        print(f"AGENT STATUS: {status['name']}")
        print(f"{'='*60}")
        print(f"📋 Session: {status['session_id'][:8] if status['session_id'] else 'Not started'}")
        print(f"🎯 Capabilities: {', '.join(status['capabilities'])}")
        print(f"🧠 Memory: {status['memory_count']} items")
        print(f"📚 Knowledge: {status['knowledge_size']} entries")
        print(f"🔧 Tools: {status['registered_tools']} registered")
        print(f"👥 Team: {'Yes' if status['in_team'] else 'No'}")
        print(f"{'='*60}")

    def _get_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()


class SimpleToolWrapper:
    """
    Simple wrapper for creating tools from functions.
    Makes it easy to turn any function into a tool.
    """

    @staticmethod
    def from_function(func, name: Optional[str] = None):
        """Create a tool from a function."""
        if name is None:
            name = func.__name__

        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__name__ = name
        wrapper.__doc__ = func.__doc__

        return wrapper


# Example tools for testing
def tool_file_read(path: str) -> str:
    """Read a file and return its contents."""
    with open(path, 'r') as f:
        return f.read()


def tool_file_write(path: str, content: str) -> bool:
    """Write content to a file."""
    with open(path, 'w') as f:
        f.write(content)
    return True


def tool_math_add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


def tool_math_multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


def tool_shell_command(command: str) -> str:
    """Execute a shell command and return output."""
    import subprocess
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else result.stderr
