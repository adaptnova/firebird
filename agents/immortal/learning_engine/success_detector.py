"""Success Detector - Identifies what makes executions successful."""

import logging
from typing import Dict, List, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SuccessDetector:
    """Analyzes successful executions to identify success factors."""

    def __init__(self):
        self.success_cache = {}

    def analyze_successful_executions(self, executions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze a set of successful executions to extract patterns."""
        successful = [e for e in executions if e.get("status") == "completed"]

        if not successful:
            return {"message": "No successful executions to analyze"}

        analysis = {
            "total_successful": len(successful),
            "total_executions": len(executions),
            "success_rate": len(successful) / len(executions) if executions else 0,
            "factors": []
        }

        # Factor 1: Tool usage diversity
        tool_counts = [len(e.get("tool_calls", [])) for e in successful]
        if tool_counts:
            avg_tools = sum(tool_counts) / len(tool_counts)
            analysis["factors"].append({
                "factor": "optimal_tool_diversity",
                "value": avg_tools,
                "description": f"Successful executions use an average of {avg_tools:.1f} tools",
                "recommendation": f"Provide agents with {max(2, int(avg_tools))}-{int(avg_tools + 2)} relevant tools"
            })

        # Factor 2: Duration analysis
        durations = [e.get("duration_seconds", 0) for e in successful if e.get("duration_seconds")]
        if durations:
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)

            analysis["factors"].append({
                "factor": "optimal_duration",
                "avg_seconds": avg_duration,
                "range_seconds": [min_duration, max_duration],
                "description": f"Successful tasks take {avg_duration:.0f}s on average",
                "recommendation": f"Set timeout thresholds to {int(max_duration * 1.5)}s"
            })

        # Factor 3: Common tools
        tool_frequency = {}
        for execution in successful:
            for call in execution.get("tool_calls", []):
                tool_name = call.get("activity_type", "unknown")
                tool_frequency[tool_name] = tool_frequency.get(tool_name, 0) + 1

        if tool_frequency:
            most_common = sorted(tool_frequency.items(), key=lambda x: x[1], reverse=True)[:3]
            analysis["factors"].append({
                "factor": "essential_tools",
                "top_tools": most_common,
                "description": f"Most successful executions use {', '.join([t[0] for t in most_common])}",
                "recommendation": "Ensure these tools are available and well-maintained"
            })

        # Factor 4: Agent type patterns
        agent_success = {}
        for execution in executions:
            agent_type = execution.get("agent_type", "unknown")
            if agent_type not in agent_success:
                agent_success[agent_type] = {"total": 0, "successful": 0}
            agent_success[agent_type]["total"] += 1
            if execution.get("status") == "completed":
                agent_success[agent_type]["successful"] += 1

        best_agents = []
        for agent_type, stats in agent_success.items():
            if stats["total"] >= 3:  # Only consider agents with enough data
                rate = stats["successful"] / stats["total"]
                if rate > 0.8:  # High success rate
                    best_agents.append((agent_type, rate))

        if best_agents:
            analysis["factors"].append({
                "factor": "high_performing_agents",
                "agents": best_agents,
                "description": f"Agents with >80% success rate: {', '.join([a[0] for a in best_agents])}",
                "recommendation": "Study these agents' configurations and replicate"
            })

        logger.info(f"Success analysis complete. Found {len(analysis['factors'])} success factors")
        return analysis

    def detect_improvement_opportunities(self, executions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify opportunities for improvement based on successful patterns."""
        opportunities = []

        # Find patterns in successful executions that could be synthesized
        successful = [e for e in executions if e.get("status") == "completed"]

        if len(successful) < 3:
            return opportunities

        # Look for tool sequences that appear in successful executions
        from collections import defaultdict
        sequence_counts = defaultdict(int)

        for execution in successful:
            tool_calls = execution.get("tool_calls", [])
            tool_names = [call.get("activity_type", "").split(".")[-1] for call in tool_calls]

            # Track sequences of 2-3 tools
            for length in [2, 3]:
                for i in range(len(tool_names) - length + 1):
                    seq = tuple(tool_names[i:i + length])
                    sequence_counts[seq] += 1

        # Suggest tool synthesis for frequent sequences
        for seq, count in sequence_counts.items():
            if count >= 3 and len(seq) >= 3:  # Sequence of 3+ tools used 3+ times
                opportunities.append({
                    "type": "tool_synthesis",
                    "pattern": f"{' → '.join(seq)}",
                    "frequency": count,
                    "description": f"This tool sequence appears in {count} successful executions",
                    "action": f"Create a combined tool: {'_'.join(seq)}",
                    "priority": "high" if count >= 5 else "medium"
                })

        # Look for agents that could benefit from successful patterns
        all_agents = set(e.get("agent_type") for e in executions)
        successful_agents = set(e.get("agent_type") for e in successful)

        if len(all_agents) > len(successful_agents):
            struggling_agents = all_agents - successful_agents
            opportunities.append({
                "type": "knowledge_sharing",
                "agents": list(struggling_agents),
                "description": f"These agents have no successful executions: {', '.join(struggling_agents)}",
                "action": "Analyze successful agents and apply patterns to struggling ones",
                "priority": "medium"
            })

        logger.info(f"Identified {len(opportunities)} improvement opportunities")
        return opportunities


# Example usage
async def main():
    """Demo success detection."""
    # Example executions
    executions = [
        {
            "agent_type": "research",
            "status": "completed",
            "duration_seconds": 45,
            "tool_calls": [{"activity_type": "search"}],
            "error_message": None
        },
        {
            "agent_type": "research",
            "status": "completed",
            "duration_seconds": 60,
            "tool_calls": [{"activity_type": "search"}],
            "error_message": None
        },
        {
            "agent_type": "code",
            "status": "failed",
            "duration_seconds": 30,
            "tool_calls": [{"activity_type": "write_file"}],
            "error_message": "File not found"
        }
    ]

    detector = SuccessDetector()
    analysis = detector.analyze_successful_executions(executions)
    opportunities = detector.detect_improvement_opportunities(executions)

    print("Success Analysis:")
    print(f"Success rate: {analysis['success_rate']:.2%}")
    for factor in analysis['factors']:
        print(f"- {factor['factor']}: {factor['description']}")

    print(f"\nImprovement Opportunities: {len(opportunities)}")
    for opp in opportunities:
        print(f"- {opp['type']}: {opp['description']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
