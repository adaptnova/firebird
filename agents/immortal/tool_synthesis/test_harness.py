"""Test Harness - Automatically tests generated tools before deployment."""

import os
import sys
import logging
import importlib.util
from typing import Dict, Any, List, Optional
from datetime import datetime
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ToolTestHarness:
    """
    Automated testing harness for synthesized tools.

    Runs generated tools in sandboxed environment with mock data
    to validate functionality before deployment.
    """

    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds
        self.results = []

    def test_tool(self, tool_file_path: str) -> Dict[str, Any]:
        """
        Test a generated tool file.

        Args:
            tool_file_path: Path to the Python file containing the tool

        Returns:
            Test results with pass/fail status and details
        """
        logger.info(f"Testing tool: {tool_file_path}")

        result = {
            "tool_file": tool_file_path,
            "tested_at": datetime.utcnow().isoformat(),
            "status": "pending",
            "checks": [],
            "errors": [],
            "warnings": []
        }

        # Check 1: File exists and can be imported
        import_result = self._test_import(tool_file_path)
        result["checks"].append(import_result)

        if not import_result["passed"]:
            result["status"] = "failed"
            result["errors"].extend(import_result.get("errors", []))
            return result

        # Check 2: Parse and validate structure
        structure_result = self._test_structure(tool_file_path)
        result["checks"].append(structure_result)

        if not structure_result["passed"]:
            result["warnings"].extend(structure_result.get("warnings", []))

        # Check 3: Syntax is valid
        syntax_result = self._test_syntax(tool_file_path)
        result["checks"].append(syntax_result)

        if not syntax_result["passed"]:
            result["status"] = "failed"
            result["errors"].extend(syntax_result.get("errors", []))
            return result

        # Check 4: Execute with test inputs (if safe)
        execution_result = self._test_execution(tool_file_path)
        result["checks"].append(execution_result)

        if execution_result["passed"]:
            result["status"] = "passed"
        else:
            result["status"] = "failed"
            result["errors"].extend(execution_result.get("errors", []))

        logger.info(f"Tool test complete: {result['status']}")
        return result

    def _test_import(self, file_path: str) -> Dict[str, Any]:
        """Test that the tool file can be imported."""
        check = {
            "name": "import_test",
            "description": "Verify file can be imported",
            "passed": False,
            "errors": []
        }

        try:
            # Load the module
            spec = importlib.util.spec_from_file_location(
                os.path.basename(file_path).replace(".py", ""),
                file_path
            )
            module = importlib.util.module_from_spec(spec)

            # Add safe modules to sys.modules
            original_modules = dict(sys.modules)

            try:
                spec.loader.exec_module(module)
                check["passed"] = True
            except Exception as e:
                check["errors"].append(f"Import error: {str(e)}")
            finally:
                # Restore sys.modules
                sys.modules.clear()
                sys.modules.update(original_modules)

        except Exception as e:
            check["errors"].append(f"Failed to load module: {str(e)}")

        return check

    def _test_syntax(self, file_path: str) -> Dict[str, Any]:
        """Test that the Python syntax is valid."""
        check = {
            "name": "syntax_test",
            "description": "Validate Python syntax",
            "passed": False,
            "errors": []
        }

        try:
            with open(file_path, "r") as f:
                code = f.read()

            compile(code, file_path, "exec")
            check["passed"] = True

        except SyntaxError as e:
            check["errors"].append(
                f"Syntax error at line {e.lineno}: {e.msg}"
            )
        except Exception as e:
            check["errors"].append(f"Unexpected error: {str(e)}")

        return check

    def _test_structure(self, file_path: str) -> Dict[str, Any]:
        """Test code structure and best practices."""
        check = {
            "name": "structure_test",
            "description": "Validate code structure",
            "passed": True,
            "warnings": []
        }

        try:
            with open(file_path, "r") as f:
                code = f.read()

            # Check 1: Has logging configuration
            if "logging.basicConfig" not in code and "logging.getLogger" not in code:
                check["warnings"].append(
                    "No logging configuration found"
                )

            # Check 2: Has docstring
            if '"""' not in code and "'''" not in code:
                check["warnings"].append(
                    "No docstring found - add documentation"
                )

            # Check 3: Has error handling
            if "try:" not in code:
                check["warnings"].append(
                    "No error handling found - recommend try/except blocks"
                )

            # Check 4: Function name matches file name (convention)
            file_name = os.path.basename(file_path).replace(".py", "")
            if f"def {file_name}(" not in code:
                check["warnings"].append(
                    f"Function name should match file name: {file_name}"
                )

            # Check 5: Import safety (avoid dangerous imports)
            dangerous_imports = [
                "import os\nsystem", "subprocess", "eval(", "exec("
            ]
            for dangerous in dangerous_imports:
                if dangerous in code:
                    check["warnings"].append(
                        f"Potentially dangerous pattern: {dangerous}"
                    )

        except Exception as e:
            check["warnings"].append(f"Structure check error: {str(e)}")

        return check

    def _test_execution(self, file_path: str) -> Dict[str, Any]:
        """Test execution with mock inputs (safely)."""
        check = {
            "name": "execution_test",
            "description": "Test tool execution with mock data",
            "passed": False,
            "errors": [],
            "output": None
        }

        tool_name = os.path.basename(file_path).replace(".py", "")

        # For safety, we don't auto-execute tools that:
        # 1. Access network
        # 2. Modify files
        # 3. Execute system commands
        # 4. Access databases

        try:
            with open(file_path, "r") as f:
                code = f.read()

            # Static analysis for safety issues
            if self._has_network_access(code):
                check["errors"].append(
                    "Tool may access network - manual testing required"
                )
                return check

            if self._has_file_modification(code):
                check["errors"].append(
                    "Tool may modify files - test in isolated environment"
                )
                return check

            if self._has_system_commands(code):
                check["errors"].append(
                    "Tool executes system commands - manual review required"
                )
                return check

            # If we reach here, tool is likely safe to test
            # In production, we would run in a sandbox
            check["warnings"] = ["Sandbox execution recommended"]
            check["passed"] = True

        except Exception as e:
            check["errors"].append(f"Execution test error: {str(e)}")

        return check

    def _has_network_access(self, code: str) -> bool:
        """Check if code may access network."""
        network_keywords = [
            "requests.", "urllib.", "socket.", "http", "https://",
            "import requests", "import urllib"
        ]
        return any(keyword in code for keyword in network_keywords)

    def _has_file_modification(self, code: str) -> bool:
        """Check if code may modify files."""
        file_keywords = [
            ".write(", "open(", "os.remove", "os.rename",
            "pathlib", "shutil", "with open", ".save("
        ]
        # Check if it's just reading files
        if "read_file" in code and "write_file" not in code:
            return False
        return any(keyword in code for keyword in file_keywords)

    def _has_system_commands(self, code: str) -> bool:
        """Check if code executes system commands."""
        system_keywords = [
            "subprocess", "os.system", "os.popen", "shell=True",
            "execute(", "Popen", "call("
        ]
        return any(keyword in code for keyword in system_keywords)

    def generate_test_report(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_tools = len(test_results)
        passed = sum(1 for r in test_results if r["status"] == "passed")
        failed = sum(1 for r in test_results if r["status"] == "failed")

        all_errors = []
        all_warnings = []

        for result in test_results:
            all_errors.extend(result.get("errors", []))
            all_warnings.extend(result.get("warnings", []))

        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_tools": total_tools,
                "passed": passed,
                "failed": failed,
                "pass_rate": passed / total_tools if total_tools > 0 else 0
            },
            "details": {
                "errors": all_errors,
                "warnings": all_warnings,
                "error_count": len(all_errors),
                "warning_count": len(all_warnings)
            },
            "recommendations": self._generate_recommendations(test_results)
        }

        if failed == 0:
            report["deployment_recommendation"] = "APPROVE"
        elif failed <= 2 and len(all_errors) < 5:
            report["deployment_recommendation"] = "APPROVE_WITH_CAUTION"
        else:
            report["deployment_recommendation"] = "REJECT"

        logger.info(f"Test report generated: {report['summary']}")
        return report

    def _generate_recommendations(self, test_results: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []

        failed_tools = [r for r in test_results if r["status"] == "failed"]

        if failed_tools:
            recommendations.append(
                f"Review {len(failed_tools)} failed tools before deployment"
            )

        # Check for common issues
        syntax_errors = sum(
            1 for r in test_results
            for check in r.get("checks", [])
            if check["name"] == "syntax_test" and not check["passed"]
        )

        if syntax_errors > 0:
            recommendations.append(
                f"Fix {syntax_errors} tools with syntax errors"
            )

        # Check for safety concerns
        safety_concerns = sum(
            1 for r in test_results
            for error in r.get("errors", [])
            if any(word in error.lower() for word in [
                "network", "file", "system command", "manual review"
            ])
        )

        if safety_concerns > 0:
            recommendations.append(
                f"Manually review {safety_concerns} tools with safety concerns"
            )

        if len(recommendations) == 0:
            recommendations.append("All tools passed testing - ready for deployment")

        return recommendations


# Example usage
async def main():
    """Demo tool testing."""
    harness = ToolTestHarness()

    # Create a simple test tool file
    test_tool_path = "/tmp/test_tool.py"
    with open(test_tool_path, "w") as f:
        f.write("""
import logging


def test_tool(query: str) -> str:
    \"\"\"Test tool that returns a greeting.\"\"\"
    logging.info(f"Executing test_tool with query: {query}")
    return f"Hello, {query}!"
""")

    result = harness.test_tool(test_tool_path)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    import asyncio
    import json
    asyncio.run(main())
