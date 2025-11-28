"""Temporal Worker for Research Workflows"""

import asyncio
import temporalio
from temporalio.worker import Worker
from temporal_research_workflows import (
    AutonomousResearchWorkflow,
    ResearchOrchestrator,
    research_activity,
    generate_report_activity,
)


async def main():
    """Start the Temporal worker for research workflows"""
    print("=" * 80)
    print("TEMPORAL RESEARCH WORKER")
    print("=" * 80)
    print()
    print("Registering workflows:")
    print("  - AutonomousResearchWorkflow")
    print("  - ResearchOrchestrator")
    print()
    print("Registering activities:")
    print("  - research_activity")
    print("  - generate_report_activity")
    print()

    # Create worker
    worker = Worker(
        client=await temporalio.client.Client.connect("localhost:7233"),
        task_queue="research-tasks",
        workflows=[AutonomousResearchWorkflow, ResearchOrchestrator],
        activities=[research_activity, generate_report_activity],
    )

    print("✅ Worker ready!")
    print("  Task Queue: research-tasks")
    print()
    print("🔄 Listening for workflows...")
    print()

    # Run worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
