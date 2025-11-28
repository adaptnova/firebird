"""REAL Temporal Workflows for Autonomous AI Research - 20 Workers"""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Any
import aiohttp
from tavily import TavilyClient
import temporalio
from temporalio import workflow, activity
from temporalio.client import Client
from datetime import timedelta

# Research topics for 20 Temporal workflows
RESEARCH_TOPICS = [
    "Temporal workflow patterns for AI agents",
    "Durable execution in multi-agent systems",
    "Agent orchestration patterns with Temporal",
    "Crash-proof AI agent architectures",
    "Temporal activities for AI workflows",
    "Event sourcing in agent systems",
    "AI agent persistence strategies",
    "Temporal workflows for autonomous agents",
    "Multi-agent coordination with Temporal",
    "Agent state management Temporal",
    "AI agent workflows crash recovery",
    "Temporal in production AI systems",
    "Temporal vs AWS Step Functions AI",
    "Agent messaging with Temporal",
    "AI agent orchestration LangGraph Temporal",
    "Temporal activities async AI agents",
    "Agent workflow durability patterns",
    "AI agent temporal workflows best practices",
    "Temporal in multi-agent architecture",
    "Autonomous AI systems Temporal case studies"
]


# Temporal Activities (the actual work)
@activity.defn
async def research_activity(topic: str) -> Dict[str, Any]:
    """Conduct research on a topic using Tavily"""
    print(f"[Temporal Activity] Researching: {topic}")

    # Search for information
    tavily_client = TavilyClient()
    results = await asyncio.to_thread(
        tavily_client.search,
        query=topic,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True,
        max_results=10,
    )

    # Extract sources
    sources = [
        {
            'title': r['title'],
            'url': r['url'],
            'content': r.get('content', r.get('snippet', '')),
            'query': topic
        }
        for r in results.get('results', [])
    ]

    # Analyze
    all_content = ' '.join([s['content'] for s in sources[:5]])
    key_concepts = [
        "Temporal workflows",
        "Durable execution",
        "Agent orchestration",
        "Crash recovery",
        "Multi-agent systems",
        "AI agents",
        "Event sourcing",
        "State management",
        "Persistence",
        "Coordination"
    ]
    found_concepts = [c for c in key_concepts if c.lower() in all_content.lower()]

    return {
        'topic': topic,
        'sources': sources,
        'key_concepts': found_concepts,
        'total_sources': len(sources),
        'concepts_found': len(found_concepts),
        'coverage': len(found_concepts) / len(key_concepts),
        'timestamp': datetime.now().isoformat()
    }


@activity.defn
async def generate_report_activity(research_data: Dict[str, Any]) -> str:
    """Generate a report from research data"""
    print(f"[Temporal Activity] Generating report for: {research_data['topic'][:50]}...")

    # Create report
    report = {
        'topic': research_data['topic'],
        'timestamp': research_data['timestamp'],
        'executive_summary': f"Research on '{research_data['topic']}' completed. Found {research_data['total_sources']} sources with {research_data['concepts_found']} key concepts identified. Coverage: {research_data['coverage']:.1%}",
        'key_findings': [
            f"Identified {research_data['total_sources']} relevant sources",
            f"Found {research_data['concepts_found']} key concepts related to Temporal and AI agents",
            f"Coverage score: {research_data['coverage']:.1%}",
            "Research completed via Temporal workflows"
        ],
        'sources': research_data['sources'][:5],
        'key_concepts': research_data['key_concepts'],
        'recommendations': [
            f"Further research needed on: {', '.join(research_data['key_concepts'][:3])}",
            "Explore Temporal's workflow retry mechanisms",
            "Investigate agent orchestration patterns",
            "Consider event sourcing for agent state"
        ]
    }

    # Save report
    filename = f"reports/temporal_worker_{research_data['topic'].replace(' ', '_')[:30]}.json"
    filepath = f"/adapt/projects/firebird/{filename}"

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"[Temporal Activity] Saved: {filename}")
    return filepath


# Temporal Workflows (the durable execution)
@workflow.defn
class AutonomousResearchWorkflow:
    """Temporal workflow for autonomous research"""

    @workflow.run
    async def run(self, topic: str) -> str:
        """Execute research workflow"""
        print(f"[Temporal Workflow] Starting research on: {topic}")

        # Execute research activity
        research_data = await workflow.execute_activity(
            research_activity,
            topic,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=workflow.RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
                backoff_coefficient=2.0,
                maximum_attempts=3,
            )
        )

        # Generate report
        report_path = await workflow.execute_activity(
            generate_report_activity,
            research_data,
            start_to_close_timeout=timedelta(minutes=1),
        )

        print(f"[Temporal Workflow] Completed: {topic[:50]}...")
        return report_path


@workflow.defn
class ResearchOrchestrator:
    """Orchestrate multiple research workflows"""

    @workflow.run
    async def run_all(self, topics: List[str]) -> List[str]:
        """Execute all research workflows in parallel"""
        print(f"[Orchestrator] Launching {len(topics)} research workflows...")

        # Execute all workflows in parallel using TaskGroup
        async with workflow.TaskGroup() as tg:
            tasks = [
                tg.create_task(
                    workflow.execute_child_workflow(
                        "AutonomousResearchWorkflow",
                        topic,
                        id=f"research-{i}-{topic.replace(' ', '_')[:20]}",
                        task_queue="research-tasks",
                        start_to_close_timeout=timedelta(minutes=5),
                    )
                )
                for i, topic in enumerate(topics, 1)
            ]

        # Collect results
        results = [task.result() for task in tasks]

        print(f"[Orchestrator] All {len(results)} workflows completed!")
        return results


async def run_temporal_research_swarm():
    """Run 20 Temporal research workflows"""
    print("=" * 80)
    print("🚀 TEMPORAL AUTONOMOUS AI RESEARCH - 20 WORKFLOWS")
    print("   Real Temporal Workflows with Durable Execution")
    print("=" * 80)
    print()

    # Connect to Temporal server
    print("📡 Connecting to Temporal server...")
    client = await Client.connect("localhost:7233")
    print("✅ Connected!")
    print()

    # Start orchestrator workflow
    print(f"🎯 Launching Research Orchestrator...")
    print()

    start_time = datetime.now()

    handle = await client.start_workflow(
        "ResearchOrchestrator.run_all",
        RESEARCH_TOPICS,
        id="research-orchestrator-2025",
        task_queue="research-tasks",
        start_to_close_timeout=timedelta(minutes=10),
    )

    print("⏳ Waiting for all workflows to complete...")
    results = await handle.result()

    duration = (datetime.now() - start_time).total_seconds()

    print()
    print("=" * 80)
    print("✅ TEMPORAL RESEARCH SWARM COMPLETE!")
    print("=" * 80)
    print(f"⏱️  Total Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"👥 Workflows Completed: {len(results)}/20")
    print(f"📊 Reports Generated: {len(results)}")
    print()
    print("🎉 All reports saved to /adapt/projects/firebird/reports/")
    print("📈 Check Temporal UI: http://localhost:8080")
    print("=" * 80)

    # Generate executive summary
    print("\n📋 Generating executive summary...")
    all_sources = []
    all_concepts = []

    # This would require loading the reports to aggregate
    print("✅ Executive summary would be generated here")


if __name__ == "__main__":
    asyncio.run(run_temporal_research_swarm())
