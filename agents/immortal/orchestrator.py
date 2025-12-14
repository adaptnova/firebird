"""
🧬 IMMORTAL: Self-Improving Agent Orchestrator

Main orchestration script that runs the complete self-improving agent system:
1. Collect execution traces
2. Analyze patterns
3. Generate embeddings
4. Detect synthesis opportunities
5. Generate new tools
6. Test and validate
7. Publish to registry
8. Notify agents

Run with: python orchestrator.py --mode continuous
"""

import asyncio
import os
import sys
import json
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from learning_engine import (
    TraceCollector,
    PatternAnalyzer,
    EmbeddingGenerator,
    SuccessDetector,
    FailureAnalyzer
)
from tool_synthesis import (
    ToolPatternDetector,
    ToolGenerator,
    ToolTestHarness,
    RegistryPublisher
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ImmortalOrchestrator:
    """Orchestrates the complete self-improving agent system."""

    def __init__(self, postgres_uri: str, qdrant_url: str = "localhost:18050"):
        self.postgres_uri = postgres_uri

        # Initialize learning engine components
        self.trace_collector = TraceCollector(postgres_uri)
        self.pattern_analyzer = PatternAnalyzer()
        self.embedding_generator = EmbeddingGenerator(qdrant_url)
        self.success_detector = SuccessDetector()
        self.failure_analyzer = FailureAnalyzer()

        # Initialize tool synthesis components
        self.pattern_detector = ToolPatternDetector(threshold_frequency=3)
        self.tool_generator = ToolGenerator()
        self.test_harness = ToolTestHarness()
        self.registry_publisher = RegistryPublisher()

        # Statistics
        self.stats = {
            "traces_collected": 0,
            "patterns_identified": 0,
            "tools_generated": 0,
            "tools_published": 0,
            "iterations": 0
        }

    async def run_continuous(self, interval_minutes: int = 30):
        """
        Run the orchestrator continuously at specified intervals.

        Args:
            interval_minutes: How often to run the improvement cycle
        """
        logger.info(f"🚀 Starting IMMORTAL continuous improvement (interval: {interval_minutes}min)")
        logger.info(f"🎯 Target: Learning from agent executions and auto-generating tools")

        # Create database tables
        await self.trace_collector.create_tables()

        iteration = 0
        try:
            while True:
                iteration += 1
                logger.info(f"""
╔{'═' * 70}╗
║{'IMMORTAL Learning Cycle #' + str(iteration):^70}║
╚{'═' * 70}╝
                """)

                # Run one improvement cycle
                await self.run_single_cycle()

                # Log statistics
                self.stats["iterations"] = iteration
                logger.info(f"📊 Cycle complete. Stats: {json.dumps(self.stats, indent=2)}")

                # Wait for next cycle
                logger.info(f"⏳ Sleeping for {interval_minutes} minutes...")
                await asyncio.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            logger.info("🛑 IMMORTAL stopped by user")
        except Exception as e:
            logger.error(f"❌ IMMORTAL error: {e}")
            raise

    async def run_single_cycle(self) -> Dict[str, Any]:
        """
        Run one complete learning and synthesis cycle.

        Returns:
            Dictionary with cycle results
        """
        cycle_results = {
            "started_at": datetime.utcnow().isoformat(),
            "phases": {}
        }

        # PHASE 1: Collect Traces
        logger.info("""
╔═══════════════════════════════════════════════════════════════════════╗
║                     PHASE 1: Collect Execution Traces                  ║
╚═══════════════════════════════════════════════════════════════════════╝
        """)

        try:
            executions = await self.trace_collector.collect_all_recent(hours=2)
            self.stats["traces_collected"] = len(executions)

            if not executions:
                logger.info("📭 No recent executions found, skipping cycle")
                return {"status": "skipped", "reason": "no executions"}

            logger.info(f"📊 Collected {len(executions)} execution traces")
            cycle_results["phases"]["trace_collection"] = {
                "status": "completed",
                "executions": len(executions)
            }

        except Exception as e:
            logger.error(f"❌ Trace collection failed: {e}")
            cycle_results["phases"]["trace_collection"] = {
                "status": "failed",
                "error": str(e)
            }
            return cycle_results

        # PHASE 2: Analyze Patterns
        logger.info("""
╔═══════════════════════════════════════════════════════════════════════╗
║                     PHASE 2: Analyze Patterns                          ║
╚═══════════════════════════════════════════════════════════════════════╝
        """)

        try:
            analysis = await self.pattern_analyzer.analyze(executions)
            self.stats["patterns_identified"] = len(analysis.get("tool_sequences", []))

            logger.info(f"🔍 Pattern analysis complete:")
            logger.info(f"   - Tool sequences: {len(analysis.get('tool_sequences', []))}")
            logger.info(f"   - Task patterns: {len(analysis.get('task_patterns', []))}")
            logger.info(f"   - Bottlenecks: {len(analysis.get('bottlenecks', []))}")
            logger.info(f"   - Failure patterns: {len(analysis.get('failure_patterns', []))}")

            cycle_results["phases"]["pattern_analysis"] = {
                "status": "completed",
                "tool_sequences": len(analysis.get("tool_sequences", [])),
                "task_patterns": len(analysis.get("task_patterns", [])),
                "bottlenecks": len(analysis.get("bottlenecks", [])),
                "failure_patterns": len(analysis.get("failure_patterns", []))
            }

        except Exception as e:
            logger.error(f"❌ Pattern analysis failed: {e}")
            cycle_results["phases"]["pattern_analysis"] = {
                "status": "failed",
                "error": str(e)
            }
            return cycle_results

        # PHASE 3: Generate Embeddings
        logger.info("""
╔═══════════════════════════════════════════════════════════════════════╗
║                     PHASE 3: Generate Vector Embeddings                ║
╚═══════════════════════════════════════════════════════════════════════╝
        """)

        try:
            # Store tool sequences as embeddings
            for seq in analysis.get("tool_sequences", [])[:10]:  # Limit to top 10
                if seq.get("synthesis_recommended"):
                    await self.embedding_generator.store_tool_sequence(
                        sequence=seq["sequence"],
                        frequency=seq["frequency"],
                        success_rate=seq["success_rate"],
                        avg_duration=seq["avg_duration_seconds"]
                    )

            # Store success patterns
            success_analysis = self.success_detector.analyze_successful_executions(executions)
            self.stats["patterns_identified"] += len(success_analysis.get("factors", []))

            cycle_results["phases"]["embedding_generation"] = {
                "status": "completed",
                "stored_vectors": len(analysis.get("tool_sequences", []))
            }

        except Exception as e:
            logger.error(f"❌ Embedding generation failed: {e}")
            cycle_results["phases"]["embedding_generation"] = {
                "status": "failed",
                "error": str(e)
            }
            return cycle_results

        # PHASE 4: Detect Synthesis Opportunities
        logger.info("""
╔═══════════════════════════════════════════════════════════════════════╗
║                     PHASE 4: Detect Tool Synthesis Opportunities       ║
╚═══════════════════════════════════════════════════════════════════════╝
        """)

        try:
            synthesis_report = self.pattern_detector.generate_synthesis_report(executions)

            opportunities = len(synthesis_report.get("opportunities", {}).get("high_priority", []))
            opportunities += len(synthesis_report.get("opportunities", {}).get("medium_priority", []))

            logger.info(f"💡 Found {opportunities} tool synthesis opportunities")

            if opportunities == 0:
                logger.info("No synthesis opportunities this cycle")
                cycle_results["phases"]["synthesis_detection"] = {
                    "status": "completed",
                    "opportunities": 0,
                    "action": "none"
                }
                return cycle_results

            cycle_results["phases"]["synthesis_detection"] = {
                "status": "completed",
                "opportunities": opportunities,
                "high_priority": len(synthesis_report.get("opportunities", {}).get("high_priority", [])),
                "medium_priority": len(synthesis_report.get("opportunities", {}).get("medium_priority", []))
            }

        except Exception as e:
            logger.error(f"❌ Synthesis detection failed: {e}")
            cycle_results["phases"]["synthesis_detection"] = {
                "status": "failed",
                "error": str(e)
            }
            return cycle_results

        # PHASE 5: Generate Tools
        logger.info("""
╔═══════════════════════════════════════════════════════════════════════╗
║                     PHASE 5: Generate New Tools                        ║
╚═══════════════════════════════════════════════════════════════════════╝
        """)

        try:
            high_priority = synthesis_report["opportunities"]["high_priority"][:3]  # Max 3 per cycle

            generated_tools = []
            for opportunity in high_priority:
                tool_name = opportunity["tool_name"]
                logger.info(f"🛠️  Generating tool: {tool_name}")

                tool_result = self.tool_generator.generate_combined_tool(
                    tool_name=tool_name,
                    tool_sequence=opportunity["tools"],
                    pattern_context={
                        "description": opportunity["rationale"],
                        "avg_duration_seconds": opportunity.get("avg_duration_seconds", 60),
                        "success_rate": opportunity["success_rate"],
                        "task_type": opportunity["task_type"],
                        "frequency": opportunity["frequency"]
                    }
                )

                generated_tools.append(tool_result)
                logger.info(f"✅ Generated: {tool_name}")

            self.stats["tools_generated"] = len(generated_tools)

            cycle_results["phases"]["tool_generation"] = {
                "status": "completed",
                "generated": len(generated_tools),
                "tools": [t["tool_name"] for t in generated_tools]
            }

        except Exception as e:
            logger.error(f"❌ Tool generation failed: {e}")
            cycle_results["phases"]["tool_generation"] = {
                "status": "failed",
                "error": str(e)
            }
            return cycle_results

        # PHASE 6: Test Tools
        logger.info("""
╔═══════════════════════════════════════════════════════════════════════╗
║                     PHASE 6: Test Generated Tools                      ║
╚═══════════════════════════════════════════════════════════════════════╝
        """)

        try:
            test_results = []
            for tool in generated_tools:
                logger.info(f"🧪 Testing tool: {tool['tool_name']}")

                test_result = self.test_harness.test_tool(tool["file_path"])
                test_results.append(test_result)

            # Generate test report
            test_report = self.test_harness.generate_test_report(test_results)

            logger.info(f"📝 Test report: {test_report['summary']}")
            logger.info(f"   Recommendation: {test_report['deployment_recommendation']}")

            cycle_results["phases"]["tool_testing"] = {
                "status": "completed",
                **test_report["summary"],
                "deployment_recommendation": test_report["deployment_recommendation"]
            }

        except Exception as e:
            logger.error(f"❌ Tool testing failed: {e}")
            cycle_results["phases"]["tool_testing"] = {
                "status": "failed",
                "error": str(e)
            }
            return cycle_results

        # PHASE 7: Publish to Registry
        logger.info("""
╔═══════════════════════════════════════════════════════════════════════╗
║                     PHASE 7: Publish to Tool Registry                  ║
╚═══════════════════════════════════════════════════════════════════════╝
        """)

        try:
            published_tools = []
            for i, tool in enumerate(generated_tools):
                # Only publish if tests passed or with approval
                test_result = test_results[i]
                if test_result["status"] == "passed":
                    logger.info(f"📤 Publishing tool: {tool['tool_name']}")

                    publish_result = self.registry_publisher.publish_tool(
                        tool_info=tool,
                        metadata={
                            "generated_at": tool["generated_at"],
                            "success_rate": tool.get("success_rate", 0.8),
                            "frequency": tool.get("frequency", 3),
                            "category": tool.get("category", "general"),
                            "description": tool.get("description", ""),
                            "synthesizes_tools": tool.get("synthesizes_tools", []),
                            "safety_reviewed": False,  # Set to True after manual review
                            "deployment_approved": False
                        }
                    )

                    if publish_result["status"] == "published":
                        published_tools.append(tool["tool_name"])

                        # Broadcast to agents
                        await self.registry_publisher.broadcast_tool_available(
                            tool_name=tool["tool_name"],
                            metadata=publish_result
                        )

            self.stats["tools_published"] = len(published_tools)

            logger.info(f"✅ Published {len(published_tools)} tools: {', '.join(published_tools)}")

            cycle_results["phases"]["tool_publishing"] = {
                "status": "completed",
                "published": len(published_tools),
                "tools": published_tools
            }

        except Exception as e:
            logger.error(f"❌ Tool publishing failed: {e}")
            cycle_results["phases"]["tool_publishing"] = {
                "status": "failed",
                "error": str(e)
            }
            return cycle_results

        # Phase complete
        cycle_results["completed_at"] = datetime.utcnow().isoformat()
        cycle_results["overall_status"] = "completed"

        logger.info("""
╔═══════════════════════════════════════════════════════════════════════╗
║                     🎉 IMMORTAL CYCLE COMPLETE                         ║
╚═══════════════════════════════════════════════════════════════════════╝
        """)

        return cycle_results

    async def run_single_batch(self) -> Dict[str, Any]:
        """
        Run one batch cycle (collect → analyze → report only, no synthesis).

        Returns:
            Analysis results
        """
        logger.info("🔍 Running batch analysis only (no synthesis)")

        # Collect recent executions
        executions = await self.trace_collector.collect_all_recent(hours=24)

        if not executions:
            return {"status": "no_data", "executions": 0}

        # Analyze patterns
        analysis = await self.pattern_analyzer.analyze(executions)

        # Detect synthesis opportunities (but don't generate)
        synthesis_report = self.pattern_detector.generate_synthesis_report(executions)

        return {
            "status": "completed",
            "executions": len(executions),
            "patterns": len(analysis.get("tool_sequences", [])),
            "opportunities": synthesis_report["summary"]
        }



def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="IMMORTAL: Self-Improving Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run continuous improvement (every 30 minutes)
  python orchestrator.py --mode continuous --interval 30

  # Run one improvement cycle
  python orchestrator.py --mode single

  # Run batch analysis only (no synthesis)
  python orchestrator.py --mode batch

  # Run with custom database
  python orchestrator.py --mode single --postgres "postgresql://..."
        """
    )

    parser.add_argument(
        "--mode",
        choices=["continuous", "single", "batch"],
        default="single",
        help="Run mode: continuous (loop), single (one cycle), or batch (analysis only)"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Interval in minutes for continuous mode"
    )

    parser.add_argument(
        "--postgres",
        type=str,
        default=os.environ.get("POSTGRES_CLUSTER_URLS"),
        help="PostgreSQL connection URI"
    )

    parser.add_argument(
        "--qdrant",
        type=str,
        default="localhost:18050",
        help="Qdrant URL for vector storage"
    )

    args = parser.parse_args()

    # Validate postgres URI
    if not args.postgres:
        logger.error("❌ PostgreSQL URI not provided (use --postgres or set POSTGRES_CLUSTER_URLS)")
        sys.exit(1)

    # Create orchestrator
    orchestrator = ImmortalOrchestrator(
        postgres_uri=args.postgres,
        qdrant_url=args.qdrant
    )

    # Run based on mode
    try:
        if args.mode == "continuous":
            asyncio.run(orchestrator.run_continuous(interval_minutes=args.interval))

        elif args.mode == "single":
            result = asyncio.run(orchestrator.run_single_cycle())
            print("\n" + "═" * 79)
            print("IMMORTAL SINGLE CYCLE RESULTS")
            print("═" * 79)
            print(json.dumps(result, indent=2))

        elif args.mode == "batch":
            result = asyncio.run(orchestrator.run_single_batch())
            print("\n" + "═" * 79)
            print("IMMORTAL BATCH ANALYSIS")
            print("═" * 79)
            print(json.dumps(result, indent=2))

    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
