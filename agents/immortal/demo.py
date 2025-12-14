"""
🧬 IMMORTAL Demo Script

Demonstrates the self-improving agent system with mock data.
Run without database connectivity to show how the system works.
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path

# Add paths
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

from tool_synthesis.pattern_detector import ToolPatternDetector
from tool_synthesis.tool_generator import ToolGenerator
from tool_synthesis.test_harness import ToolTestHarness
from tool_synthesis.registry_publisher import RegistryPublisher
from learning_engine.pattern_analyzer import PatternAnalyzer
from learning_engine.success_detector import SuccessDetector
from learning_engine.failure_analyzer import FailureAnalyzer

print("🧬" * 40)
print("IMMORTAL: Self-Improving Agent System Demo")
print("🧬" * 40)
print()


# Create mock execution data
def create_mock_executions():
    """Create realistic mock execution traces."""
    print("📊 Creating mock execution data...")

    return [
        # Success pattern: Research workflow
        {
            "workflow_id": f"research_wf_{i:03d}",
            "agent_type": "research",
            "status": "completed",
            "duration_seconds": 45 + (i % 10),
            "tool_calls": [
                {"activity_type": "search_web", "input": {"query": "AI trends 2025"}},
                {"activity_type": "parse_html", "input": {"url": "example.com"}},
                {"activity_type": "extract_data", "input": {"pattern": "trends"}},
                {"activity_type": "summarize", "input": {"text": "..."}},
            ],
            "task_description": "Research AI trends",
            "error_message": None
        }
        for i in range(8)  # 8 successful research workflows
    ] + [
        # Success pattern: Code workflow
        {
            "workflow_id": f"code_wf_{i:03d}",
            "agent_type": "code",
            "status": "completed",
            "duration_seconds": 120 + (i * 5),
            "tool_calls": [
                {"activity_type": "read_file", "input": {"path": "/src/app.py"}},
                {"activity_type": "analyze_code", "input": {"content": "..."}},
                {"activity_type": "edit_file", "input": {"old": "x", "new": "y"}},
                {"activity_type": "run_tests", "input": {"path": "/tests"}},
            ],
            "task_description": "Fix bug in app.py",
            "error_message": None
        }
        for i in range(5)  # 5 successful code workflows
    ] + [
        # Failure patterns
        {
            "workflow_id": f"fail_wf_{i:03d}",
            "agent_type": "research",
            "status": "failed",
            "duration_seconds": 300,
            "tool_calls": [
                {"activity_type": "search_api", "input": {"query": "..."}},
            ],
            "task_description": "Search with API",
            "error_message": "API rate limit exceeded"
        }
        for i in range(3)  # 3 failed executions
    ] + [
        {
            "workflow_id": f"fail_timeout_{i:03d}",
            "agent_type": "code",
            "status": "failed",
            "duration_seconds": 600,
            "tool_calls": [
                {"activity_type": "run_tests", "input": {"path": "/tests"}},
            ],
            "task_description": "Run test suite",
            "error_message": "Timeout after 10 minutes"
        }
        for i in range(2)  # 2 timeout failures
    ]


async def demo_pattern_detection():
    """Demo: Detect synthesis opportunities in execution traces."""
    print("=" * 79)
    print("DEMO 1: Pattern Detection")
    print("=" * 79)
    print()

    executions = create_mock_executions()
    print(f"✅ Created {len(executions)} mock executions")
    print("   - 8 research workflows (search → parse → extract → summarize)")
    print("   - 5 code workflows (read → analyze → edit → test)")
    print("   - 3 API failures (rate limit)")
    print("   - 2 timeout failures")
    print()

    detector = ToolPatternDetector(threshold_frequency=3)
    report = detector.generate_synthesis_report(executions)

    print(f"📈 Analysis Results:")
    print(f"   • Tool sequences found: {len(report['detailed_patterns']['tool_sequences'])}")
    print(f"   • Parameter patterns: {len(report['detailed_patterns']['parameter_patterns'])}")
    print(f"   • Cross-tool patterns: {len(report['detailed_patterns']['cross_tool_patterns'])}")
    print()

    print(f"💡 Synthesis Opportunities:")
    print(f"   • High priority: {report['summary']['high_priority']}")
    print(f"   • Medium priority: {report['summary']['medium_priority']}")
    print(f"   • Total: {report['summary']['total_opportunities']}")
    print()

    if report['summary']['high_priority'] > 0:
        print("🔥 High Priority Opportunities:")
        for opp in report['opportunities']['high_priority']:
            print(f"\n   → Tool: {opp['tool_name']}")
            print(f"     Tools: {' → '.join(opp['tools'])}")
            print(f"     Frequency: {opp['frequency']}")
            print(f"     Success Rate: {opp['success_rate']:.1%}")
            print(f"     Why: {opp['rationale']}")

    print()
    return report


async def demo_analyze_success():
    """Demo: Analyze successful executions."""
    print("=" * 79)
    print("DEMO 2: Success Analysis")
    print("=" * 79)
    print()

    executions = create_mock_executions()
    detector = SuccessDetector()

    analysis = detector.analyze_successful_executions(executions)

    print(f"📊 Success Analysis:")
    print(f"   • Total executions: {analysis['total_executions']}")
    print(f"   • Successful: {analysis['total_successful']}")
    print(f"   • Success rate: {analysis['success_rate']:.1%}")
    print()

    print(f"🎯 Success Factors:")
    for factor in analysis['factors']:
        print(f"\n   → {factor['factor'].replace('_', ' ').title()}")
        print(f"     {factor['description']}")
        print(f"     💡 {factor['recommendation']}")

    print()

    opportunities = detector.detect_improvement_opportunities(executions)
    if opportunities:
        print(f"🚀 Improvement Opportunities:")
        for opp in opportunities:
            print(f"\n   → {opp['type'].replace('_', ' ').title()}")
            print(f"     Action: {opp['action']}")
            print(f"     Priority: {opp['priority']}")

    print()


async def demo_analyze_failures():
    """Demo: Analyze failure patterns."""
    print("=" * 79)
    print("DEMO 3: Failure Analysis")
    print("=" * 79)
    print()

    executions = create_mock_executions()
    analyzer = FailureAnalyzer()

    analysis = analyzer.analyze(executions)

    print(f"❌ Failure Analysis:")
    print(f"   • Total failures: {analysis['total_failures']}")
    print(f"   • Failure rate: {analysis['failure_rate']:.1%}")
    print()

    print(f"📊 Failure Categories:")
    for cat in analysis['categories']:
        print(f"   • {cat['category']}: {cat['count']} ({cat['percentage']:.1%})")
        if cat['example_error']:
            print(f"     Example: {cat['example_error'][:80]}...")

    print()

    if analysis['tool_failures']:
        print(f"🔧 Tool Failure Patterns:")
        for fail in analysis['tool_failures'][:3]:
            print(f"\n   → Tool: {fail['tool']}")
            print(f"     Failures: {fail['failure_count']}")
            print(f"     Severity: {fail['severity']}")
            print(f"     Fix: {fail['recommendation']}")

    print()


async def demo_generate_tools():
    """Demo: Generate tools from patterns."""
    print("=" * 79)
    print("DEMO 4: Tool Generation")
    print("=" * 79)
    print()

    executions = create_mock_executions()
    detector = ToolPatternDetector(threshold_frequency=3)
    report = detector.generate_synthesis_report(executions)

    if not report['opportunities']['high_priority']:
        print("⚠️  No high-priority synthesis opportunities in demo data")
        print()
        return

    generator = ToolGenerator()
    harness = ToolTestHarness()

    print(f"🛠️  Generating Tools:")
    print()

    generated_tools = []
    for opp in report['opportunities']['high_priority'][:2]:  # Generate max 2
        print(f"   → Generating: {opp['tool_name']}")

        tool_result = generator.generate_combined_tool(
            tool_name=opp['tool_name'],
            tool_sequence=opp['tools'],
            pattern_context={
                'description': opp['rationale'],
                'avg_duration_seconds': opp.get('avg_duration_seconds', 60),
                'success_rate': opp['success_rate'],
                'task_type': opp['task_type'],
                'frequency': opp['frequency']
            }
        )

        generated_tools.append(tool_result)

        print(f"     ✅ Generated: {tool_result['tool_name']}")
        print(f"     📄 File: {tool_result['file_path']}")

        # Test the tool
        print(f"     🧪 Testing...")
        test_result = harness.test_tool(tool_result['file_path'])
        print(f"     📊 Test result: {test_result['status'].upper()}")

        # Show code preview
        print(f"     💻 Code preview:")
        code_lines = tool_result['code'].split('\n')[:15]
        for i, line in enumerate(code_lines, 1):
            print(f"        {i:2d} | {line}")
        if len(tool_result['code'].split('\n')) > 15:
            print(f"        ... ({len(tool_result['code'].split(chr(10))) - 15} more lines)")

        print()

    print(f"✅ Generated {len(generated_tools)} new tools!")
    print()


async def demo_publishing():
    """Demo: Publish to registry and notify agents."""
    print("=" * 79)
    print("DEMO 5: Registry Publishing")
    print("=" * 79)
    print()

    # Create a simple tool
    tool_code = '''def demo_tool(query: str) -> str:
    """Demo tool that returns a greeting."""
    import logging
    logging.info(f"Executing demo_tool with: {query}")
    return f"Hello from IMMORTAL! You asked: {query}"
'''

    tool_path = "/tmp/demo_tool.py"
    with open(tool_path, "w") as f:
        f.write(tool_code)

    publisher = RegistryPublisher()

    print(f"📤 Publishing demo_tool to registry...")

    result = publisher.publish_tool(
        tool_info={
            'tool_name': 'demo_tool',
            'file_path': tool_path
        },
        metadata={
            'generated_at': datetime.now().isoformat(),
            'success_rate': 0.95,
            'frequency': 10,
            'category': 'demo',
            'description': 'Demo tool for IMMORTAL presentation'
        }
    )

    print(f"   ✅ Status: {result['status'].upper()}")
    if result['status'] == 'published':
        print(f"   📍 File: {result['file_path']}")

    print()

    # Get registry stats
    stats = publisher.get_registry_stats()
    print(f"📊 Registry Stats:")
    for key, value in stats.items():
        print(f"   • {key.replace('_', ' ').title()}: {value}")

    print()


async def main():
    """Run all demos."""
    print()
    print("🎬 Starting IMMORTAL Demos")
    print("=" * 79)
    print()

    # Run demos
    await demo_pattern_detection()
    await demo_analyze_success()
    await demo_analyze_failures()
    await demo_generate_tools()
    await demo_publishing()

    # Summary
    print("=" * 79)
    print("🎉 IMMORTAL Demo Complete!")
    print("=" * 79)
    print()
    print("✨ What you just saw:")
    print("   1. Pattern detection from execution traces")
    print("   2. Success/failure analysis")
    print("   3. Automatic tool generation")
    print("   4. Tool testing and validation")
    print("   5. Registry publishing")
    print()
    print("🚀 Ready to run with real data? Try:")
    print("   python agents/immortal/orchestrator.py --mode single")
    print()


if __name__ == "__main__":
    asyncio.run(main())
