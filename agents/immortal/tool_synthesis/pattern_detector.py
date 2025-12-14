"""Tool Pattern Detector - Identifies opportunities for tool synthesis."""

import logging
from typing import Dict, List, Any, Tuple
from collections import defaultdict
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ToolPatternDetector:
    """Detects patterns in tool usage that could be synthesized into new tools."""

    def __init__(self, threshold_frequency: int = 3):
        """
        Initialize pattern detector.

        Args:
            threshold_frequency: Minimum times a pattern must appear to be considered
        """
        self.threshold_frequency = threshold_frequency

    def detect_tool_sequences(self, executions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect sequences of tools that are frequently used together.

        Returns:
            List of patterns with tools, frequency, and attributes
        """
        sequence_counts = defaultdict(list)  # (seq, task_type) -> [execution_ids]
        sequence_durations = defaultdict(list)  # (seq) -> [durations]
        sequence_success = defaultdict(list)  # (seq) -> [success_status]

        for execution in executions:
            tool_calls = execution.get("tool_calls", [])
            if not tool_calls:
                continue

            task_type = self._categorize_task(execution)
            duration = execution.get("duration_seconds", 0)
            success = execution.get("status") == "completed"

            tool_names = []
            for call in tool_calls:
                activity_type = call.get("activity_type", "")
                tool_name = self._extract_tool_name(activity_type)
                tool_names.append(tool_name)

            # Look for sequences of different lengths
            for length in [2, 3, 4, 5]:
                if len(tool_names) >= length:
                    for i in range(len(tool_names) - length + 1):
                        seq = tuple(tool_names[i:i + length])
                        pattern_key = (seq, task_type)

                        sequence_counts[pattern_key].append(execution.get("workflow_id"))
                        sequence_durations[seq].append(duration)
                        sequence_success[seq].append(success)

        # Filter sequences that meet threshold
        patterns = []
        for (seq, task_type), exec_ids in sequence_counts.items():
            freq = len(exec_ids)

            if freq >= self.threshold_frequency:
                # Calculate average duration
                durations = sequence_durations[seq]
                avg_duration = sum(durations) / len(durations) if durations else 0

                # Calculate success rate
                successes = sequence_success[seq]
                success_rate = sum(successes) / len(successes) if successes else 0

                # Auto-generate tool name
                tool_name = self._generate_tool_name(seq)

                patterns.append({
                    "tools": list(seq),
                    "tool_name": tool_name,
                    "frequency": freq,
                    "task_type": task_type,
                    "avg_duration_seconds": avg_duration,
                    "success_rate": success_rate,
                    "exec_ids": exec_ids,
                    "confidence": "high" if freq >= 5 else "medium",
                    "synthesis_recommended": success_rate >= 0.7 and len(seq) >= 3
                })

        # Sort by frequency (descending)
        patterns.sort(key=lambda x: x["frequency"], reverse=True)

        logger.info(f"Detected {len(patterns)} tool sequence patterns meeting threshold")
        return patterns

    def detect_parameter_patterns(self, executions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect common parameter patterns in tool calls.

        Example: If 'search' tool is always called with 'max_results=10',
        this could be an opportunity for tool specialization.
        """
        param_patterns = defaultdict(lambda: {"count": 0, "values": {}})

        for execution in executions:
            tool_calls = execution.get("tool_calls", [])

            for call in tool_calls:
                tool_name = self._extract_tool_name(
                    call.get("activity_type", "")
                )
                params = call.get("input", {}).get("params", {})

                # Check for frequently used parameter combinations
                param_key = str(sorted(params.items()))
                param_patterns[(tool_name, param_key)]["count"] += 1

                # Track parameter values
                for key, value in params.items():
                    if key not in param_patterns[(tool_name, param_key)]["values"]:
                        param_patterns[(tool_name, param_key)]["values"][key] = defaultdict(int)
                    param_patterns[(tool_name, param_key)]["values"][key][str(value)] += 1

        # Filter by frequency
        frequent_params = []
        for (tool_name, param_key), data in param_patterns.items():
            if data["count"] >= self.threshold_frequency:
                # Decode the param key to get actual params
                import ast
                try:
                    params_dict = dict(ast.literal_eval(param_key))
                except:
                    params_dict = {}

                frequent_params.append({
                    "tool": tool_name,
                    "parameters": params_dict,
                    "frequency": data["count"],
                    "values_distribution": {
                        k: dict(v) for k, v in data["values"].items()
                    },
                    "opportunity_type": "specialized_tool"
                })

        return frequent_params

    def detect_cross_tool_patterns(self, executions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect patterns that involve relationships between tools.

        Example: Tool A outputs files that Tool B always reads
        """
        patterns = []

        for execution in executions:
            tool_calls = execution.get("tool_calls", [])

            # Look for data flow patterns between tools
            for i in range(len(tool_calls) - 1):
                current_call = tool_calls[i]
                next_call = tool_calls[i + 1]

                current_tool = self._extract_tool_name(
                    current_call.get("activity_type", "")
                )
                next_tool = self._extract_tool_name(
                    next_call.get("activity_type", "")
                )

                # Check if next tool uses output from current tool
                current_output = current_call.get("output", {})
                next_input = next_call.get("input", {})

                if self._output_input_dependency(current_output, next_input):
                    patterns.append({
                        "pattern_type": "data_flow",
                        "producer": current_tool,
                        "consumer": next_tool,
                        "output_type": type(current_output).__name__,
                        "frequency": 1  # Would track across all executions
                    })

        return patterns

    def generate_synthesis_report(self, executions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive report of all synthesis opportunities.

        Returns:
            Report with prioritized list of tool synthesis opportunities
        """
        logger.info("Generating tool synthesis opportunities report...")

        sequences = self.detect_tool_sequences(executions)
        param_patterns = self.detect_parameter_patterns(executions)
        cross_tool = self.detect_cross_tool_patterns(executions)

        # Prioritize opportunities
        high_priority = []
        medium_priority = []

        for seq in sequences:
            if seq["synthesis_recommended"]:
                if seq["frequency"] >= 5 and seq["success_rate"] >= 0.8:
                    priority = "high"
                    priority_list = high_priority
                else:
                    priority = "medium"
                    priority_list = medium_priority

                priority_list.append({
                    "type": "tool_sequence",
                    "priority": priority,
                    "tool_name": seq["tool_name"],
                    "tools": seq["tools"],
                    "frequency": seq["frequency"],
                    "success_rate": seq["success_rate"],
                    "task_type": seq["task_type"],
                    "rationale": f"Frequent sequence with {seq['success_rate']:.0%} success rate"
                })

        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "executions_analyzed": len(executions),
            "summary": {
                "total_opportunities": len(high_priority) + len(medium_priority),
                "high_priority": len(high_priority),
                "medium_priority": len(medium_priority),
                "tool_sequences": len(sequences),
                "parameter_patterns": len(param_patterns),
                "cross_tool_patterns": len(cross_tool)
            },
            "opportunities": {
                "high_priority": high_priority,
                "medium_priority": medium_priority
            },
            "detailed_patterns": {
                "tool_sequences": sequences,
                "parameter_patterns": param_patterns,
                "cross_tool_patterns": cross_tool
            }
        }

        logger.info(f"Synthesis report generated: {report['summary']}")
        return report

    def _categorize_task(self, execution: Dict[str, Any]) -> str:
        """Categorize a task based on its description and tools used."""
        task_desc = execution.get("task_description", "").lower()

        if any(word in task_desc for word in ["research", "search", "find", "analyze"]):
            return "research"
        elif any(word in task_desc for word in ["code", "implement", "write", "fix"]):
            return "code"
        elif any(word in task_desc for word in ["test", "bug", "error", "fail"]):
            return "testing"
        else:
            # Categorize by most used tool
            tool_calls = execution.get("tool_calls", [])
            tool_names = [self._extract_tool_name(c.get("activity_type", "")) for c in tool_calls]

            if "search" in tool_names:
                return "research"
            elif "write_file" in tool_names or "read_file" in tool_names:
                return "code"
            else:
                return "general"

    def _extract_tool_name(self, activity_type: str) -> str:
        """Extract clean tool name from activity type."""
        if not activity_type:
            return "unknown"

        if "." in activity_type:
            return activity_type.split(".")[-1]

        return activity_type

    def _generate_tool_name(self, tool_sequence: Tuple[str, ...]) -> str:
        """Auto-generate a tool name from a sequence."""
        if len(tool_sequence) == 2:
            return f"{tool_sequence[0]}_{tool_sequence[1]}"
        elif len(tool_sequence) == 3:
            return f"{tool_sequence[0]}_{tool_sequence[1]}_{tool_sequence[2]}"
        else:
            # For longer sequences, use abbreviations
            abbrev = "".join([t[:3] for t in tool_sequence[:3]])
            return f"combined_{abbrev}"

    def _output_input_dependency(self, output: Dict[str, Any], input_params: Dict[str, Any]) -> bool:
        """Check if input depends on output (simple heuristic)."""
        output_str = str(output).lower()
        input_str = str(input_params).lower()

        # Simple check: do any output values appear in input
        # In production, use more sophisticated analysis
        if "file" in output_str and "file" in input_str:
            return True
        if "output" in output_str and "output" in input_str:
            return True

        return False


# Example usage
async def main():
    """Demo pattern detection."""
    # Example execution traces
    executions = [
        {
            "workflow_id": "wf_1",
            "status": "completed",
            "task_description": "Research AI trends",
            "tool_calls": [
                {"activity_type": "search_web", "input": {"query": "AI trends 2025"}},
                {"activity_type": "parse_html", "input": {"url": "example.com"}},
                {"activity_type": "extract_data", "input": {"pattern": "trends"}}
            ],
            "duration_seconds": 45
        },
        {
            "workflow_id": "wf_2",
            "status": "completed",
            "task_description": "Research ML algorithms",
            "tool_calls": [
                {"activity_type": "search_web", "input": {"query": "ML algorithms"}},
                {"activity_type": "parse_html", "input": {"url": "arxiv.org"}},
                {"activity_type": "extract_data", "input": {"pattern": "algorithms"}}
            ],
            "duration_seconds": 50
        },
        {
            "workflow_id": "wf_3",
            "status": "failed",
            "task_description": "Search for data",
            "tool_calls": [
                {"activity_type": "search_web", "input": {"query": "data"}},
                {"activity_type": "parse_html", "input": {"url": "data.gov"}}
            ],
            "duration_seconds": 30
        },
        {
            "workflow_id": "wf_4",
            "status": "completed",
            "task_description": "Research robotics",
            "tool_calls": [
                {"activity_type": "search_web", "input": {"query": "robotics 2025"}},
                {"activity_type": "parse_html", "input": {"url": "ieee.org"}},
                {"activity_type": "extract_data", "input": {"pattern": "robotics"}}
            ],
            "duration_seconds": 60
        }
    ]

    detector = ToolPatternDetector(threshold_frequency=2)
    patterns = detector.detect_tool_sequences(executions)
    report = detector.generate_synthesis_report(executions)

    print("Tool Synthesis Report:")
    print(json.dumps(report["summary"], indent=2))
    print("\nHigh Priority Opportunities:")
    for opp in report["opportunities"]["high_priority"]:
        print(f"- {opp['tool_name']}: {opp['rationale']}")


if __name__ == "__main__":
    import asyncio
    import json
    asyncio.run(main())
