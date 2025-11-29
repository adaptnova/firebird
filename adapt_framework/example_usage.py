#!/usr/bin/env python3
"""
ADAPT Framework Example Usage

Demonstrates the complete ADAPT Framework with all modules working together:
- PERSIST: Memory and state management
- KNOW: Knowledge of self/tools/team
- ACT: Tool execution and action planning
- COORDINATE: Multi-agent coordination

Run with: python3 example_usage.py
"""

import sys
import os
from pathlib import Path
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adapt_framework import PersistentMemory, KnowledgeManager
from adapt_framework.core.act import ToolRegistry, ActionExecutor, ActionPlanner
from adapt_framework.core.coordinate import TeamCoordinator
from adapt_framework.agents.adapt_agent import ADAPTAgent, SimpleToolWrapper


def example_file_read(path: str) -> str:
    """Example tool: Read a file."""
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"


def example_file_write(path: str, content: str) -> bool:
    """Example tool: Write to a file."""
    try:
        # Ensure directory exists
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing file: {e}")
        return False


def example_calculate_sum(numbers: List[float]) -> float:
    """Example tool: Calculate sum of numbers."""
    return sum(numbers)


def example_shell_echo(message: str) -> str:
    """Example tool: Echo a message."""
    return f"Echo: {message}"


def demo_basic_agent():
    """Demo 1: Basic single agent with tools."""
    print("\n" + "="*70)
    print("DEMO 1: Basic ADAPT Agent - Single Agent with Tools")
    print("="*70)

    # Create agent
    agent = ADAPTAgent(
        name="DemoAgent",
        capabilities=["file_operations", "calculations", "shell_commands"],
        memory_path="/tmp/demo_agent_memory",
        knowledge_path="/tmp/demo_agent_knowledge.json"
    )

    # Register tools
    agent.register_tool("file_read", example_file_read)
    agent.register_tool("file_write", example_file_write)
    agent.register_tool("calculate_sum", example_calculate_sum)
    agent.register_tool("shell_echo", example_shell_echo)

    # Show agent status
    agent.print_status()

    # Test: Create and write a file
    print("\n📋 TASK: Create a configuration file")
    result = agent.run(
        "Write a configuration file with database settings",
        mode="plan_build"
    )

    print(f"\n📊 Result:")
    print(f"   Mode: {result.get('mode')}")
    print(f"   Successful actions: {result.get('successful_actions', 0)}/{result.get('total_actions', 0)}")

    return agent


def demo_team_coordination():
    """Demo 2: Multiple agents working together."""
    print("\n" + "="*70)
    print("DEMO 2: Team Coordination - Multiple Agents Working Together")
    print("="*70)

    # Create team coordinator
    coordinator = TeamCoordinator()

    # Create agents
    planner = ADAPTAgent(
        name="Planner",
        capabilities=["planning", "research", "analysis"]
    )
    planner.register_tool("research", lambda query: f"Research results for: {query}")

    builder = ADAPTAgent(
        name="Builder",
        capabilities=["coding", "file_operations", "implementation"]
    )
    builder.register_tool("file_write", example_file_write)
    builder.register_tool("file_read", example_file_read)

    tester = ADAPTAgent(
        name="Tester",
        capabilities=["testing", "validation", "quality_assurance"]
    )
    tester.register_tool("test_run", lambda test_file: f"All tests passed in {test_file}")

    # Add agents to team
    planner.add_to_team(coordinator)
    builder.add_to_team(coordinator)
    tester.add_to_team(coordinator)

    print("\n👥 Team formed with 3 agents")
    print(coordinator.summary())

    # Create tasks
    task1_id = coordinator.create_task(
        task_type="research",
        description="Research best practices for API design",
        priority=4
    )

    task2_id = coordinator.create_task(
        task_type="coding",
        description="Implement REST API endpoints",
        priority=5,
        dependencies=[task1_id]
    )

    task3_id = coordinator.create_task(
        task_type="testing",
        description="Write and run tests for the API",
        priority=4,
        dependencies=[task2_id]
    )

    print(f"\n📋 Created {len(coordinator.get_pending_tasks())} tasks")

    # Delegate tasks
    coordinator.delegate(task1_id, "Planner")
    coordinator.delegate(task2_id, "Builder")
    coordinator.delegate(task3_id, "Tester")

    # Simulate task completion
    # In a real scenario, agents would actually do the work
    coordinator.mark_task_complete(task1_id, {"findings": ["Use RESTful routes", "Include auth"]})  # type: ignore
    coordinator.mark_task_complete(task2_id, {"endpoints": ["/users", "/posts"]})  # type: ignore
    coordinator.mark_task_complete(task3_id, {"test_coverage": "95%"})  # type: ignore

    print("\n📊 Coordinator Statistics:")
    stats = coordinator.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    return coordinator


def demo_memory_persistence():
    """Demo 3: Memory persistence across sessions."""
    print("\n" + "="*70)
    print("DEMO 3: Memory Persistence - Learning Across Sessions")
    print("="*70)

    memory_path = "/tmp/adapt_memory_persistence"
    knowledge_path = "/tmp/adapt_knowledge_persistence.json"

    # Session 1: Learn something
    print("\n📚 SESSION 1: Learning phase")
    agent1 = ADAPTAgent(
        name="LearningAgent",
        capabilities=["learning", "observation"],
        memory_path=memory_path,
        knowledge_path=knowledge_path
    )

    agent1.start_session("learning_session")

    # Record some learnings
    agent1.memory.save_memory(
        agent1.session_id,
        "learning",
        "The file_write tool works best with absolute paths",
        importance=0.9,
        tags=["tools", "file_operations", "best_practices"]
    )

    agent1.memory.save_memory(
        agent1.session_id,
        "learning",
        "Small tasks execute faster in direct mode",
        importance=0.7,
        tags=["performance", "optimization"]
    )

    print(f"   Saved {len(agent1.memory.recall_memory(agent1.session_id, limit=100))} learnings")

    # Session 2: Try to recall
    print("\n🧠 SESSION 2: Recall phase")
    agent2 = ADAPTAgent(
        name="RecallAgent",
        capabilities=["learning", "observation"],
        memory_path=memory_path,
        knowledge_path=knowledge_path
    )

    agent2.start_session("recall_session")

    # Recall previous learnings
    recalled = agent2.memory.recall_memory(
        memory_type="learning",
        limit=10
    )

    print(f"   Recalled {len(recalled)} learnings from previous session:")
    for i, memory in enumerate(recalled[:2], 1):
        print(f"   {i}. {memory['content'][:60]}...")

    return agent2


def demo_knowledge_awareness():
    """Demo 4: Self and tool knowledge management."""
    print("\n" + "="*70)
    print("DEMO 4: Knowledge Awareness - Self and Tool Knowledge")
    print("="*70)

    agent = ADAPTAgent(
        name="KnowledgeAgent",
        capabilities=["analysis", "self_awareness", "tool_management"]
    )

    # Register tools
    agent.register_tool("file_tool", lambda x: x, {"description": "File operations"})
    agent.register_tool("calc_tool", lambda x: x, {"description": "Calculations"})
    agent.register_tool("api_tool", lambda x: x, {"description": "API calls"})

    # Simulate tool usage and track success rates
    agent.knowledge.update_tool_stats("file_tool", success=True, execution_time=1.2)
    agent.knowledge.update_tool_stats("file_tool", success=True, execution_time=1.5)
    agent.knowledge.update_tool_stats("calc_tool", success=True, execution_time=0.5)
    agent.knowledge.update_tool_stats("api_tool", success=False, execution_time=5.0)

    # Get self-assessment
    assessment = agent.knowledge.self_assessment()

    print("\n📊 Self-Assessment:")
    print(f"   Capabilities: {assessment['capabilities']}")
    print(f"   Best tools: {', '.join(assessment['best_tools'])}")
    print(f"   Success rate: {assessment['success_rate']}")

    # Get best tools
    best_tools = agent.knowledge.get_best_tools()

    print("\n🎯 Recommended tools (based on performance):")
    for tool in best_tools:
        info = agent.knowledge.get_tool_info(tool)
        if info:
            success_rate = info.get('success_rate', 0) * 100
            print(f"   {tool}: {success_rate:.0f}% success rate")

    return agent


def main():
    """Run all demos."""
    print("\n" + "🚀"*35)
    print("ADAPT FRAMEWORK - COMPLETE DEMONSTRATION")
    print("🚀"*35)
    print("\nFramework: PERSIST + KNOW + ACT + COORDINATE")
    print("Principles: Build infrastructure that builds itself")

    try:
        # Demo 1: Basic agent
        agent = demo_basic_agent()

        # Demo 2: Team coordination
        coordinator = demo_team_coordination()

        # Demo 3: Memory persistence
        agent_with_memory = demo_memory_persistence()

        # Demo 4: Knowledge awareness
        knowledgeable_agent = demo_knowledge_awareness()

        # Summary
        print("\n" + "="*70)
        print("🎉 ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*70)

        print("\n✨ Key Features Demonstrated:")
        print("   ✓ Tool execution with error handling")
        print("   ✓ Action planning and batch execution")
        print("   ✓ Multi-agent team coordination")
        print("   ✓ Cross-session memory persistence")
        print("   ✓ Self and tool knowledge management")
        print("   ✓ Task delegation and tracking")
        print("   ✓ Performance metrics and statistics")

        print("\n📁 Files created:")
        for path in ["/tmp/demo_file.txt", "/tmp/demo_agent_memory", "/tmp/adapt_memory_persistence"]:
            if Path(path).exists():
                print(f"   ✓ {path}")

        print("\n" + "🚀"*35)
        print("NEXT: Build infrastructure that builds itself!")
        print("🚀"*35 + "\n")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
