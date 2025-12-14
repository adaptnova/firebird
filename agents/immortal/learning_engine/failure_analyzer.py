"""Failure Analyzer - Identifies failure patterns and root causes."""

import json
import logging
from typing import Dict, List, Any
from collections import defaultdict

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FailureAnalyzer:
    """Analyzes failed executions to identify patterns and root causes."""

    def __init__(self):
        import os
        model_name = os.environ.get("MiniMax_M2_MODEL", "minimax-m2")
        base_url = os.environ.get("MiniMax_M2_BASE_URL", "https://api.minimax.io/anthropic")
        self.llm = ChatAnthropic(
            model=model_name,
            temperature=0,
            base_url=base_url
        )

        self.failure_prompt = PromptTemplate(
            input_variables=["failed_executions"],
            template="""
You are analyzing failed AI agent executions to identify patterns and root causes.

Failed executions:
{failed_executions}

For each failure, identify:
1. Error category (API error, timeout, logic error, tool error, etc.)
2. Root cause (what actually went wrong)
3. Prevention strategy (how to avoid in the future)
4. Whether this represents a pattern or is an isolated incident

Return your analysis as JSON:
{
  "failure_categories": {
    "timeout": 3,
    "api_error": 2,
    "logic_error": 1
  },
  "patterns": [
    {
      "pattern": "API rate limiting during parallel execution",
      "occurrences": 5,
      "category": "api_error",
      "root_cause": "Making too many concurrent API calls",
      "prevention_strategy": "Implement exponential backoff and rate limit aware scheduling",
      "severity": "high"
    }
  ],
  "isolated_incidents": [
    {
      "error": "specific error",
      "occurrence": 1,
      "recommendation": "Monitor for recurrence"
    }
  ],
  "overall_assessment": "Most failures due to API rate limits. Recommend implementing smarter scheduling."
}
"""
        )

        self.chain = self.failure_prompt | self.llm | JsonOutputParser()

    def categorize_failures(self, executions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Categorize failures by error type."""
        failures = [e for e in executions if e.get("status") == "failed"]

        if not failures:
            return []

        categories = defaultdict(list)

        for execution in failures:
            error = execution.get("error_message", "")
            error_lower = error.lower()

            # Categorize based on error message patterns
            if "timeout" in error_lower or "timed out" in error_lower:
                categories["timeout"].append(execution)
            elif "api" in error_lower or "rate limit" in error_lower:
                categories["api_error"].append(execution)
            elif any(word in error_lower for word in ["error", "exception", "failed"]):
                categories["tool_error"].append(execution)
            else:
                categories["other"].append(execution)

        categorized = []
        for category, executions_list in categories.items():
            categorized.append({
                "category": category,
                "count": len(executions_list),
                "percentage": len(executions_list) / len(failures) if failures else 0,
                "example_error": executions_list[0].get("error_message", "")[:200] if executions_list else ""
            })

        return sorted(categorized, key=lambda x: x["count"], reverse=True)

    def identify_retry_opportunities(self, failures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify failures that might succeed on retry."""
        transient_errors = [
            "timeout",
            "rate limit",
            "connection",
            "network",
            "service unavailable"
        ]

        retry_candidates = []

        for execution in failures:
            error = execution.get("error_message", "").lower()

            is_transient = any(err in error for err in transient_errors)

            if is_transient:
                retry_candidates.append({
                    "execution_id": execution.get("workflow_id"),
                    "error": error[:100],
                    "retry_likely": True,
                    "priority": "high"
                })

        return retry_candidates

    def extract_tool_failure_patterns(self, failures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify which tools are causing failures."""
        tool_failures = {}

        for execution in failures:
            error = execution.get("error_message", "")
            tool_calls = execution.get("tool_calls", [])

            for call in tool_calls:
                tool_name = call.get("activity_type", "").split(".")[-1]

                if tool_name not in tool_failures:
                    tool_failures[tool_name] = {
                        "count": 0,
                        "errors": defaultdict(int)
                    }

                tool_failures[tool_name]["count"] += 1

                # Try to match error to tool
                if tool_name.lower() in error.lower():
                    error_summary = error[:150] if len(error) > 150 else error
                    tool_failures[tool_name]["errors"][error_summary] += 1

        # Convert to list format
        patterns = []
        for tool_name, data in tool_failures.items():
            if data["count"] >= 2:  # Tool failed multiple times
                patterns.append({
                    "tool": tool_name,
                    "failure_count": data["count"],
                    "common_errors": dict(data["errors"]),
                    "recommendation": f"Review and improve {tool_name} tool",
                    "severity": "high" if data["count"] >= 5 else "medium"
                })

        return sorted(patterns, key=lambda x: x["failure_count"], reverse=True)

    def analyze(self, executions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Comprehensive failure analysis."""
        failures = [e for e in executions if e.get("status") == "failed"]

        if not failures:
            return {"message": "No failures to analyze"}

        logger.info(f"Analyzing {len(failures)} failures...")

        analysis = {
            "total_failures": len(failures),
            "failure_rate": len(failures) / len(executions) if executions else 0,
            "categories": self.categorize_failures(executions),
            "tool_failures": self.extract_tool_failure_patterns(failures),
            "retry_opportunities": self.identify_retry_opportunities(failures),
        }

        logger.info(f"Failure analysis complete. Found {len(analysis['categories'])} categories")
        return analysis


# Example usage
async def main():
    """Demo failure analysis."""
    executions = [
        {
            "agent_type": "research",
            "status": "failed",
            "duration_seconds": 120,
            "tool_calls": [{"activity_type": "search_api"}],
            "error_message": "API rate limit exceeded",
            "agent_type": "research"
        },
        {
            "agent_type": "research",
            "status": "failed",
            "duration_seconds": 300,
            "tool_calls": [{"activity_type": "search_api"}],
            "error_message": "Timeout after 300 seconds",
            "agent_type": "research"
        },
        {
            "agent_type": "code",
            "status": "failed",
            "duration_seconds": 30,
            "tool_calls": [{"activity_type": "write_file"}],
            "error_message": "Permission denied",
            "agent_type": "code"
        }
    ]

    analyzer = FailureAnalyzer()
    analysis = analyzer.analyze(executions)

    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    import asyncio
    import json
    asyncio.run(main())
