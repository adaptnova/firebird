"""Pattern Analyzer - Identifies patterns in agent execution traces."""

import json
import logging
from collections import defaultdict, Counter
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PatternAnalyzer:
    """Analyzes execution traces to identify recurring patterns and insights."""

    def __init__(self, llm=None):
        if llm is None:
            import os
            model_name = os.environ.get("MiniMax_M2_MODEL", "minimax-m2")
            base_url = os.environ.get("MiniMax_M2_BASE_URL", "https://api.minimax.io/anthropic")
            self.llm = ChatAnthropic(
                model=model_name,
                temperature=0,
                base_url=base_url
            )
        else:
            self.llm = llm

        self.pattern_prompt = PromptTemplate(
            input_variables=["executions"],
            template="""
You are a pattern recognition expert analyzing AI agent execution traces.

Analyze the following execution traces and identify patterns, common sequences,
and opportunities for optimization.

Executions:
{executions}

Identify:
1. Common tool usage sequences (e.g., "search → parse → extract")
2. Frequently repeated task patterns
3. Bottlenecks or inefficiencies
4. Opportunities for tool synthesis
5. Success factors in completed tasks
6. Failure patterns in failed tasks

Return your analysis as JSON with this structure:
{{
  "tool_sequences": [
    {{
      "sequence": ["tool1", "tool2", "tool3"],
      "frequency": 5,
      "avg_duration_seconds": 120,
      "success_rate": 0.85,
      "recommendation": "Consider creating a combined tool"
    }}
  ],
  "task_patterns": [
    {{
      "pattern": "description of pattern",
      "occurrences": 10,
      "success_rate": 0.90,
      "tool_synthesis_opportunity": true/false
    }}
  ],
  "bottlenecks": [
    {{
      "tool": "tool_name",
      "avg_duration": 300,
      "frequency": 8,
      "impact": "high"
    }}
  ],
  "failure_patterns": [
    {{
      "pattern": "description",
      "occurrence_rate": 0.30,
      "root_cause": "analysis",
      "prevention_strategy": "recommendation"
    }}
  ],
  "success_factors": [
    {{
      "factor": "description",
      "tasks_impacted": 15,
      "recommendation": "Apply to similar tasks"
    }}
  ]
}}
"""
        )

        self.chain = self.pattern_prompt | self.llm | JsonOutputParser()

    def analyze_tool_sequences(self, executions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze tool usage sequences to find common patterns."""
        sequences = []

        for execution in executions:
            tool_calls = execution.get("tool_calls", [])

            # Extract tool names from activity types
            tool_names = []
            for call in tool_calls:
                activity_type = call.get("activity_type", "")
                # Extract tool name from activity type
                if "." in activity_type:
                    tool_name = activity_type.split(".")[-1]
                else:
                    tool_name = activity_type
                tool_names.append(tool_name)

            if len(tool_names) >= 2:  # Only interested in sequences
                sequences.append(tool_names)

        # Count frequency of sequences
        sequence_counts = defaultdict(list)  # sequence_key -> [durations]

        for seq in sequences:
            # Look at sequences of length 2, 3, 4
            for length in [2, 3, 4]:
                for i in range(len(seq) - length + 1):
                    subseq = tuple(seq[i:i + length])
                    sequence_counts[subseq].append(1)  # Count occurrences

        # Filter sequences that appear multiple times
        frequent_sequences = []
        for seq, occurrences in sequence_counts.items():
            freq = len(occurrences)
            if freq >= 3:  # Appears at least 3 times
                frequent_sequences.append({
                    "sequence": list(seq),
                    "frequency": freq,
                    "recommendation": "Consider creating a combined tool" if len(seq) >= 3 else None
                })

        # Sort by frequency
        frequent_sequences.sort(key=lambda x: x["frequency"], reverse=True)

        return frequent_sequences[:10]  # Top 10 sequences

    def analyze_task_patterns(self, executions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze task descriptions to identify common patterns."""
        tasks_by_type = defaultdict(list)

        for execution in executions:
            task_desc = execution.get("task_description", "")
            if not task_desc:
                continue

            # Categorize by keywords
            task_desc_lower = task_desc.lower()
            if "research" in task_desc_lower or "analyze" in task_desc_lower:
                tasks_by_type["research"].append(execution)
            elif "code" in task_desc_lower or "implement" in task_desc_lower:
                tasks_by_type["code"].append(execution)
            elif "test" in task_desc_lower or "bug" in task_desc_lower:
                tasks_by_type["testing"].append(execution)
            else:
                tasks_by_type["general"].append(execution)

        patterns = []

        for task_type, executions in tasks_by_type.items():
            if len(executions) < 3:
                continue

            successful = [e for e in executions if e.get("status") == "completed"]
            success_rate = len(successful) / len(executions) if executions else 0

            patterns.append({
                "pattern": f"{task_type}_tasks",
                "description": f"{len(executions)} {task_type} tasks",
                "occurrences": len(executions),
                "success_rate": success_rate,
                "tool_synthesis_opportunity": len(executions) >= 5 and success_rate < 0.8
            })

        return patterns

    def identify_bottlenecks(self, executions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify tools or steps that cause delays."""
        tool_stats = defaultdict(lambda: {"total_duration": 0, "count": 0})

        for execution in executions:
            tool_calls = execution.get("tool_calls", [])

            # Estimate duration per tool (for MVP, just count occurrences)
            for call in tool_calls:
                activity_type = call.get("activity_type", "")
                if "." in activity_type:
                    tool_name = activity_type.split(".")[-1]
                else:
                    tool_name = activity_type

                tool_stats[tool_name]["count"] += 1

                # If we have actual duration data, use it
                if "duration_seconds" in call:
                    tool_stats[tool_name]["total_duration"] += call["duration_seconds"]

        bottlenecks = []
        for tool_name, stats in tool_stats.items():
            avg_duration = stats["total_duration"] / stats["count"] if stats["count"] > 0 else 0

            # Flag as bottleneck if: appears frequently OR takes long time
            if stats["count"] >= 5 or avg_duration > 60:  # 60+ seconds
                bottlenecks.append({
                    "tool": tool_name,
                    "frequency": stats["count"],
                    "avg_duration_seconds": avg_duration,
                    "impact": "high" if avg_duration > 120 else "medium"
                })

        return sorted(bottlenecks, key=lambda x: x["avg_duration_seconds"], reverse=True)[:10]

    def analyze_failures(self, executions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze failed executions to identify failure patterns."""
        failed = [e for e in executions if e.get("status") == "failed"]

        if not failed:
            return []

        # Group by error message patterns
        error_patterns = defaultdict(list)

        for execution in failed:
            error = execution.get("error_message", "")
            # Extract error type (first line or general category)
            error_type = error.split("\n")[0][:100] if error else "unknown"
            error_patterns[error_type].append(execution)

        patterns = []
        for error_type, executions in error_patterns.items():
            if len(executions) >= 2:  # Only report patterns that appear multiple times
                rate = len(executions) / len(failed) if failed else 0
                patterns.append({
                    "pattern": error_type,
                    "occurrence_rate": rate,
                    "affected_executions": len(executions),
                    "prevention_strategy": "Review error handling for this scenario"
                })

        return patterns

    def analyze_success_factors(self, executions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify what makes tasks successful."""
        completed = [e for e in executions if e.get("status") == "completed"]

        if len(completed) < 3:
            return []

        factors = []

        # Factor 1: Tool variety
        tool_counts = [len(e.get("tool_calls", [])) for e in completed]
        avg_tools = sum(tool_counts) / len(tool_counts) if tool_counts else 0

        if avg_tools > 0:
            factors.append({
                "factor": "tool_diversity",
                "description": f"Successful tasks use an average of {avg_tools:.1f} tools",
                "tasks_impacted": len(completed),
                "recommendation": "Ensure agents have access to diverse toolsets"
            })

        # Factor 2: Duration (shorter is often better, but not too short)
        durations = [e.get("duration_seconds", 0) for e in completed if e.get("duration_seconds")]
        if durations:
            avg_duration = sum(durations) / len(durations)
            factors.append({
                "factor": "optimal_duration",
                "description": f"Optimal task duration around {avg_duration:.0f} seconds",
                "tasks_impacted": len(durations),
                "recommendation": "Set appropriate timeouts and expectations"
            })

        return factors

    async def analyze(self, executions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Comprehensive analysis of execution traces."""
        if not executions:
            return {"error": "No executions to analyze"}

        logger.info(f"Analyzing {len(executions)} executions...")

        # Basic statistical analysis
        tool_sequences = self.analyze_tool_sequences(executions)
        task_patterns = self.analyze_task_patterns(executions)
        bottlenecks = self.identify_bottlenecks(executions)
        failure_patterns = self.analyze_failures(executions)
        success_factors = self.analyze_success_factors(executions)

        # AI-powered analysis for deeper insights
        try:
            # Prepare executions data for LLM
            executions_summary = []
            for e in executions[:20]:  # Limit to 20 to avoid token limits
                executions_summary.append({
                    "task": e.get("task_description", "")[:200],
                    "status": e.get("status"),
                    "duration": e.get("duration_seconds"),
                    "tools": len(e.get("tool_calls", [])),
                    "error": e.get("error_message", "")[:100] if e.get("error_message") else None
                })

            ai_analysis = await self.chain.ainvoke({
                "executions": json.dumps(executions_summary, indent=2)
            })
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            ai_analysis = {}

        analysis = {
            "executions_analyzed": len(executions),
            "tool_sequences": tool_sequences,
            "task_patterns": task_patterns,
            "bottlenecks": bottlenecks,
            "failure_patterns": failure_patterns,
            "success_factors": success_factors,
            "ai_insights": ai_analysis,
            "generated_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Analysis complete. Found {len(tool_sequences)} sequences, "
                   f"{len(task_patterns)} patterns, {len(bottlenecks)} bottlenecks")

        return analysis


# Example usage
async def main():
    """Demo pattern analysis."""
    import os
    from trace_collector import TraceCollector

    postgres_uri = os.environ.get("POSTGRES_CLUSTER_URLS")
    if not postgres_uri:
        logger.error("POSTGRES_CLUSTER_URLS not set")
        return

    # Get recent executions
    collector = TraceCollector(postgres_uri)
    executions = await collector.get_agent_executions("research", limit=50)

    analyzer = PatternAnalyzer()
    analysis = await analyzer.analyze(executions)

    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    import asyncio
    import json
    asyncio.run(main())
