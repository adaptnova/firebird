"""
COORDINATE - Work together

Core coordination module for multi-agent collaboration and task delegation.
Implements the 'COORDINATE' principle from PACK-I.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid


@dataclass
class Task:
    """Represents a task to be executed."""

    id: str
    type: str
    description: str
    priority: int  # 1-5, where 5 is highest
    assigned_to: Optional[str]
    status: str  # 'pending', 'in_progress', 'completed', 'failed'
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    result: Optional[Any]
    error: Optional[str]
    metadata: Optional[Dict[str, Any]]
    dependencies: List[str]  # Task IDs this depends on


@dataclass
class Message:
    """Message for inter-agent communication."""

    id: str
    sender: str
    recipient: str
    type: str  # 'request', 'response', 'notification', 'delegation'
    content: Any
    timestamp: str
    requires_response: bool
    response_to: Optional[str]


class TeamCoordinator:
    """
    Coordinates multiple agents and manages task distribution.
    Enables agents to work together effectively.
    """

    def __init__(self, knowledge_manager: Optional[Any] = None):
        """
        Initialize team coordinator.

        Args:
            knowledge_manager: Optional knowledge manager for team insights
        """
        self.agents: Dict[str, Any] = {}  # agent_name -> agent_instance
        self.tasks: Dict[str, Task] = {}
        self.message_queue: List[Message] = []
        self.message_handlers: Dict[str, Callable] = {}
        self.knowledge = knowledge_manager

        # Statistics
        self.stats = {
            "tasks_created": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "messages_sent": 0,
            "average_task_duration": 0.0
        }

    def register_agent(self, name: str, agent: Any, capabilities: List[str]):
        """
        Register an agent with the coordinator.

        Args:
            name: Agent name
            agent: Agent instance
            capabilities: List of capabilities this agent has
        """
        self.agents[name] = {
            "instance": agent,
            "capabilities": capabilities,
            "current_task": None,
            "task_history": [],
            "status": "available"  # 'available', 'busy', 'offline'
        }

        # Register in knowledge base
        if self.knowledge and hasattr(self.knowledge, 'register_team_member'):
            self.knowledge.register_team_member(name, agent.__class__.__name__, capabilities)

        print(f"✅ Agent '{name}' registered with capabilities: {capabilities}")

    def unregister_agent(self, name: str):
        """Unregister an agent."""
        self.agents.pop(name, None)
        print(f"❌ Agent '{name}' unregistered")

    def get_available_agents(self) -> List[str]:
        """Get list of available agents."""
        return [
            name for name, info in self.agents.items()
            if info["status"] == "available"
        ]

    def get_agents_with_capability(self, capability: str) -> List[str]:
        """Find agents with a specific capability."""
        return [
            name for name, info in self.agents.items()
            if capability in info["capabilities"]
        ]

    def create_task(
        self,
        task_type: str,
        description: str,
        priority: int = 3,
        assigned_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None
    ) -> str:
        """
        Create a new task.

        Args:
            task_type: Type of task (e.g., 'research', 'code', 'review')
            description: Task description
            priority: Priority level (1-5)
            assigned_to: Optional agent to assign to
            metadata: Additional task metadata
            dependencies: List of task IDs this depends on

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())[:8]

        if dependencies is None:
            dependencies = []

        task = Task(
            id=task_id,
            type=task_type,
            description=description,
            priority=priority,
            assigned_to=assigned_to,
            status="pending",
            created_at=datetime.utcnow().isoformat(),
            started_at=None,
            completed_at=None,
            result=None,
            error=None,
            metadata=metadata or {},
            dependencies=dependencies
        )

        self.tasks[task_id] = task
        self.stats["tasks_created"] += 1

        print(f"📋 Task '{task_id}' created: {description}")
        return task_id

    def delegate(
        self,
        task_id: str,
        to_agent: Optional[str] = None
    ) -> bool:
        """
        Delegate a task to an agent.

        Args:
            task_id: Task ID
            to_agent: Optional specific agent (auto-select if None)

        Returns:
            Whether delegation was successful
        """
        if task_id not in self.tasks:
            print(f"❌ Task '{task_id}' not found")
            return False

        task = self.tasks[task_id]

        # Check if dependencies are met
        for dep_id in task.dependencies:
            if dep_id in self.tasks and self.tasks[dep_id].status != "completed":
                print(f"⏳ Task '{task_id}' waiting for dependency '{dep_id}'")
                return False

        # Auto-select agent if not specified
        if to_agent is None:
            capable_agents = self.get_agents_with_capability(task.type)
            available_agents = [a for a in capable_agents if self.agents[a]["status"] == "available"]

            if not available_agents:
                print(f"❌ No available agents for task type '{task.type}'")
                return False

            to_agent = available_agents[0]  # Simple: take first available

        # Verify agent exists and is available
        if to_agent not in self.agents:
            print(f"❌ Agent '{to_agent}' not found")
            return False

        if self.agents[to_agent]["status"] != "available":
            print(f"⚠️  Agent '{to_agent}' is not available (status: {self.agents[to_agent]['status']})")
            return False

        # Delegate the task
        task.assigned_to = to_agent
        task.status = "in_progress"
        task.started_at = datetime.utcnow().isoformat()

        self.agents[to_agent]["status"] = "busy"
        self.agents[to_agent]["current_task"] = task_id

        print(f"🎯 Task '{task_id}' delegated to {to_agent}")

        # Send delegation message to agent
        self.send_message(
            sender="coordinator",
            recipient=to_agent,
            type="delegation",
            content=task,
            requires_response=True
        )

        return True

    def send_message(
        self,
        sender: str,
        recipient: str,
        type: str,
        content: Any,
        requires_response: bool = False,
        response_to: Optional[str] = None
    ) -> str:
        """
        Send a message between agents.

        Args:
            sender: Message sender
            recipient: Message recipient
            type: Message type
            content: Message content
            requires_response: Whether a response is expected
            response_to: ID of message this is responding to

        Returns:
            Message ID
        """
        message_id = str(uuid.uuid4())[:8]

        message = Message(
            id=message_id,
            sender=sender,
            recipient=recipient,
            type=type,
            content=content,
            timestamp=datetime.utcnow().isoformat(),
            requires_response=requires_response,
            response_to=response_to
        )

        self.message_queue.append(message)
        self.stats["messages_sent"] += 1

        return message_id

    def get_messages_for(self, agent_name: str) -> List[Message]:
        """Get all messages for a specific agent."""
        return [
            msg for msg in self.message_queue
            if msg.recipient == agent_name
        ]

    def mark_task_complete(self, task_id: str, result: Any, error: Optional[str] = None):
        """
        Mark a task as completed or failed.

        Args:
            task_id: Task ID
            result: Task result
            error: Error if task failed
        """
        if task_id not in self.tasks:
            print(f"⚠️  Task '{task_id}' not found when marking complete")
            return

        task = self.tasks[task_id]
        task.status = "failed" if error else "completed"
        task.completed_at = datetime.utcnow().isoformat()
        task.result = result
        task.error = error

        # Update agent status
        agent = task.assigned_to
        if agent and agent in self.agents:
            self.agents[agent]["status"] = "available"
            self.agents[agent]["current_task"] = None
            self.agents[agent]["task_history"].append(task_id)

        # Update stats
        if error:
            self.stats["tasks_failed"] += 1
        else:
            self.stats["tasks_completed"] += 1

            # Update average task duration
            if task.started_at and task.completed_at:
                start = datetime.fromisoformat(task.started_at)
                end = datetime.fromisoformat(task.completed_at)
                duration = (end - start).total_seconds()

                old_avg = self.stats["average_task_duration"]
                total = self.stats["tasks_completed"]
                self.stats["average_task_duration"] = ((old_avg * (total - 1)) + duration) / total

        # Log completion
        status = "✅" if not error else "❌"
        print(f"{status} Task '{task_id}' {task.status}")
        if error:
            print(f"   Error: {error}")

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a task."""
        if task_id not in self.tasks:
            return None

        task = self.tasks[task_id]
        return {
            "id": task.id,
            "type": task.type,
            "status": task.status,
            "assigned_to": task.assigned_to,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "has_error": task.error is not None
        }

    def get_pending_tasks(self) -> List[str]:
        """Get list of pending task IDs."""
        return [
            task_id for task_id, task in self.tasks.items()
            if task.status == "pending"
        ]

    def get_workload_distribution(self) -> Dict[str, int]:
        """Get workload distribution across agents."""
        distribution = {}

        for agent_name in self.agents.keys():
            distribution[agent_name] = 0

        for task in self.tasks.values():
            if task.assigned_to and task.status in ["in_progress", "completed"]:
                distribution[task.assigned_to] = distribution.get(task.assigned_to, 0) + 1

        return distribution

    def broadcast(self, sender: str, type: str, content: Any):
        """
        Broadcast a message to all agents.

        Args:
            sender: Message sender
            type: Message type
            content: Message content
        """
        for agent_name in self.agents.keys():
            self.send_message(
                sender=sender,
                recipient=agent_name,
                type=type,
                content=content,
                requires_response=False
            )

    def process_message_queue(self) -> int:
        """
        Process all pending messages.
        Calls registered message handlers.

        Returns:
            Number of messages processed
        """
        if not self.message_queue:
            return 0

        processed = 0
        messages_to_process = self.message_queue.copy()
        self.message_queue.clear()

        for message in messages_to_process:
            # Find handler for message type
            handler = self.message_handlers.get(message.type)

            if handler:
                try:
                    handler(message)
                    processed += 1
                except Exception as e:
                    print(f"❌ Error processing message {message.id}: {e}")

        return processed

    def register_message_handler(self, message_type: str, handler: Callable):
        """Register a handler for a message type."""
        self.message_handlers[message_type] = handler
        print(f"📧 Handler registered for message type: {message_type}")

    def get_stats(self) -> Dict[str, Any]:
        """Get coordinator statistics."""
        return self.stats.copy()

    def reset_stats(self):
        """Reset statistics."""
        self.stats = {
            "tasks_created": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "messages_sent": 0,
            "average_task_duration": 0.0
        }

    def summary(self) -> str:
        """Get a summary of current state."""
        lines = [
            "=" * 50,
            "ADAPT Team Coordinator Summary",
            "=" * 50,
            f"Agents: {len(self.agents)}",
            f"  Available: {len(self.get_available_agents())}",
            "",
            f"Tasks: {len(self.tasks)}",
            f"  Pending: {len([t for t in self.tasks.values() if t.status == 'pending'])}",
            f"  In Progress: {len([t for t in self.tasks.values() if t.status == 'in_progress'])}",
            f"  Completed: {self.stats['tasks_completed']}",
            f"  Failed: {self.stats['tasks_failed']}",
            "",
            f"Messages: {self.stats['messages_sent']}",
            f"Message Queue: {len(self.message_queue)}",
            "",
            f"Avg Task Duration: {self.stats['average_task_duration']:.1f}s",
            "=" * 50
        ]

        return "\n".join(lines)
