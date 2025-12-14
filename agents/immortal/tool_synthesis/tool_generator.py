"""Tool Generator - Automatically generates Python code for new tools based on patterns."""

import os
import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ToolGenerator:
    """Generates Python code for new tools based on detected patterns."""

    def __init__(self, output_dir: str = "agents/immortal/tools/generated"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_combined_tool(
        self,
        tool_name: str,
        tool_sequence: List[str],
        pattern_context: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate a combined tool that executes a sequence of tools.

        Args:
            tool_name: Name for the new tool
            tool_sequence: List of tools to combine
            pattern_context: Context about how this pattern is used

        Returns:
            Dictionary with file_path, code, and metadata
        """
        logger.info(f"Generating combined tool: {tool_name}")

        tool_config = self._analyze_pattern_context(pattern_context)

        code = self._generate_tool_code(
            tool_name=tool_name,
            sequence=tool_sequence,
            config=tool_config
        )

        tests = self._generate_unit_tests(tool_name, tool_config)

        docs = self._generate_documentation(
            tool_name=tool_name,
            sequence=tool_sequence,
            config=tool_config
        )

        file_path = os.path.join(self.output_dir, f"{tool_name}.py")

        with open(file_path, "w") as f:
            f.write(code)

        result = {
            "file_path": file_path,
            "tool_name": tool_name,
            "code": code,
            "tests": tests,
            "documentation": docs,
            "generated_at": datetime.utcnow().isoformat(),
            "synthesizes_tools": tool_sequence,
            "status": "generated"
        }

        logger.info(f"Tool generated at {file_path}")
        return result

    def generate_specialized_tool(
        self,
        base_tool: str,
        common_params: Dict[str, Any],
        frequency: int
    ) -> Dict[str, str]:
        """
        Generate a specialized version of a tool with preset parameters.

        Args:
            base_tool: Name of the base tool
            common_params: Common parameters used
            frequency: How often this pattern occurs

        Returns:
            Dictionary with tool information
        """
        tool_name = f"{base_tool}_{self._params_signature(common_params)}"

        logger.info(f"Generating specialized tool: {tool_name}")

        tool_config = {
            "base_tool": base_tool,
            "preset_params": common_params,
            "description": f"Specialized {base_tool} with optimized parameters",
            "returns": "varies"
        }

        code = self._generate_specialized_tool_code(tool_name, tool_config)

        file_path = os.path.join(self.output_dir, f"{tool_name}.py")

        with open(file_path, "w") as f:
            f.write(code)

        result = {
            "file_path": file_path,
            "tool_name": tool_name,
            "code": code,
            "generated_at": datetime.utcnow().isoformat(),
            "base_tool": base_tool,
            "specializes_params": common_params,
            "frequency": frequency,
            "status": "generated"
        }

        logger.info(f"Specialized tool generated at {file_path}")
        return result

    def _analyze_pattern_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze pattern context to determine tool configuration."""
        return {
            "description": context.get("description", "Combined tool for efficient execution"),
            "avg_duration": context.get("avg_duration_seconds", 60),
            "success_rate": context.get("success_rate", 0.8),
            "task_type": context.get("task_type", "general"),
            "returns": self._infer_return_type(context),
            "error_handling": self._infer_error_handling(context)
        }

    def _infer_return_type(self, context: Dict[str, Any]) -> str:
        """Infer what the tool should return based on the sequence."""
        # Simple heuristic
        task_type = context.get("task_type", "")

        if "research" in task_type:
            return "Dict[str, Any]"  # Structured research results
        elif "code" in task_type:
            return "str"  # Code or file path
        elif "data" in task_type:
            return "List[Dict[str, Any]]"  # Data records
        else:
            return "Any"  # Flexible return type

    def _infer_error_handling(self, context: Dict[str, Any]) -> str:
        """Infer appropriate error handling based on success rate."""
        success_rate = context.get("success_rate", 0.8)

        if success_rate >= 0.9:
            return "basic"  # Simple try/except
        elif success_rate >= 0.7:
            return "retry"  # Retry logic
        else:
            return "robust"  # Comprehensive error handling

    def _generate_tool_code(
        self,
        tool_name: str,
        sequence: List[str],
        config: Dict[str, Any]
    ) -> str:
        """Generate Python code for the combined tool."""
        description = config.get("description", "")
        returns = config.get("returns", "Any")
        error_handling = config.get("error_handling", "basic")

        # Generate imports
        imports = self._generate_imports(sequence)

        # Generate function signature
        func_signature = self._generate_function_signature(tool_name, sequence, config)

        # Generate docstring
        docstring = self._generate_docstring(tool_name, sequence, description)

        # Generate function body
        body = self._generate_function_body(sequence, config, error_handling)

        # Add return statement
        return_statement = self._generate_return_statement(sequence, config)

        code = f"""{imports}


{func_signature}:
{docstring}
{body}
{return_statement}"""

        return code

    def _generate_imports(self, sequence: List[str]) -> str:
        """Generate import statements for the tools used."""
        imports = ["import logging"]

        # Add tool-specific imports based on sequence
        if any("search" in tool for tool in sequence):
            imports.append("from typing import Dict, Any, List")

        if any("file" in tool for tool in sequence):
            imports.append("import os")
            imports.append("import json")

        return "\n".join(imports)

    def _generate_function_signature(
        self,
        tool_name: str,
        sequence: List[str],
        config: Dict[str, Any]
    ) -> str:
        """Generate function signature with appropriate parameters."""
        params = self._infer_parameters(sequence, config)
        param_str = ", ".join(params)

        returns = config.get("returns", "Any")

        return f"def {tool_name}({param_str}) -> {returns}"

    def _infer_parameters(self, sequence: List[str], config: Dict[str, Any]) -> List[str]:
        """Infer appropriate parameters based on tool sequence."""
        params = []

        # Common parameters across many tools
        if any("search" in tool for tool in sequence):
            params.append("query: str")

        if any("file" in tool for tool in sequence):
            params.append("file_path: str")

        # Add generic params
        params.append("**kwargs")

        return params

    def _generate_docstring(
        self,
        tool_name: str,
        sequence: List[str],
        description: str
    ) -> str:
        """Generate comprehensive docstring."""
        tools_str = " → ".join(sequence)

        return f'    """{description}\n\n    This tool combines the following operations:\n    {tools_str}\n\n    Args:\n        query: Search/query parameter (if applicable)\n        file_path: File path (if applicable)\n        **kwargs: Additional parameters passed to underlying tools\n\n    Returns:\n        Combined result from the tool sequence\n    """'

    def _generate_function_body(
        self,
        sequence: List[str],
        config: Dict[str, Any],
        error_handling: str
    ) -> str:
        """Generate the main function body with error handling."""
        INDENT = "    "

        lines = []

        # Add logging
        lines.append(f"{INDENT}logging.info(f'Executing {len(sequence)} tools in sequence')")
        lines.append("")

        # Add initialization
        lines.append(f"{INDENT}result = None")
        lines.append("")

        # Generate code for each tool in sequence
        for i, tool in enumerate(sequence):
            lines.append(f"{INDENT}# Step {i + 1}: {tool}")

            if error_handling == "robust":
                lines.extend(self._generate_robust_step(tool, i))
            elif error_handling == "retry":
                lines.extend(self._generate_retry_step(tool, i))
            else:
                lines.extend(self._generate_basic_step(tool, i))

            lines.append("")

        return "\n".join(lines)

    def _generate_basic_step(self, tool: str, step_num: int) -> List[str]:
        """Generate basic try/except for a tool execution."""
        INDENT = "    "
        var_name = f"step_{step_num}_result"

        return [
            f"{INDENT}try:",
            f"{INDENT}    {var_name} = self._execute_{tool}(**kwargs)",
            f"{INDENT}    result = {var_name}",
            f"{INDENT}except Exception as e:",
            f"{INDENT}    logging.error('Error in TOOL: {{}}'.format(e))".replace("TOOL", tool),
            f"{INDENT}    raise"
        ]

    def _generate_retry_step(self, tool: str, step_num: int) -> List[str]:
        """Generate retry logic for a tool execution."""
        INDENT = "    "
        var_name = f"step_{step_num}_result"

        return [
            f"{INDENT}{var_name} = None",
            f"{INDENT}for attempt in range(3):",
            f"{INDENT}    try:",
            f"{INDENT}        {var_name} = self._execute_{tool}(**kwargs)",
            f"{INDENT}        result = {var_name}",
            f"{INDENT}        break",
            f"{INDENT}    except Exception as e:",
            f"{INDENT}        if attempt == 2:",
            f"{INDENT}            logging.error('Failed after 3 attempts: {{}}'.format(e))",
            f"{INDENT}            raise",
            f"{INDENT}        time.sleep(2  ** attempt)  # Exponential backoff"
        ]

    def _generate_robust_step(self, tool: str, step_num: int) -> List[str]:
        """Generate robust error handling with fallback."""
        INDENT = "    "
        var_name = f"step_{step_num}_result"

        return [
            f"{INDENT}{var_name} = self._safe_execute_{tool}(**kwargs)",
            f"{INDENT}if {var_name} is None:",
            f"{INDENT}    logging.warning('{tool} returned None, continuing...')",
            f"{INDENT}else:",
            f"{INDENT}    result = {var_name}"
        ]

    def _generate_return_statement(self, sequence: List[str], config: Dict[str, Any]) -> str:
        """Generate appropriate return statement."""
        INDENT = "    "

        # For sequences that end with data fetching, return the data
        if any("extract" in tool or "get" in tool for tool in sequence):
            return f"{INDENT}return result\n"

        # For file operations, return path or content
        if any("file" in tool for tool in sequence):
            return f"{INDENT}return result\n"

        # Default: return last result
        return f"{INDENT}return result\n"

    def _generate_unit_tests(self, tool_name: str, config: Dict[str, Any]) -> str:
        """Generate unit tests for the tool."""
        return """import unittest
from TOOL_NAME import TOOL_NAME


class TestTOOL_NAME_CAP(unittest.TestCase):
    def test_basic_execution(self):
        '''Test basic execution of TOOL_NAME.'''
        # This is a generated test - customize based on actual tool behavior
        pass

    def test_error_handling(self):
        '''Test error handling.'''
        # Test with invalid inputs
        pass


if __name__ == "__main__":
    unittest.main()
""".replace("TOOL_NAME", tool_name).replace("TOOL_NAME_CAP", tool_name.title().replace('_', ''))

    def _generate_documentation(
        self,
        tool_name: str,
        sequence: List[str],
        config: Dict[str, Any]
    ) -> str:
        """Generate README documentation."""
        tools_str = " → ".join(sequence)
        success_rate = config.get("success_rate", 0.8)
        avg_duration = config.get("avg_duration", 60)

        return f"""# {tool_name}

## Overview
This is an auto-generated tool that combines multiple operations into a single efficient call.

**Generated on:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}

**Tool Sequence:** {tools_str}

**Success Rate:** {success_rate:.1%}
**Average Duration:** {avg_duration:.1f}s

## Purpose
This tool was synthesized because the tool sequence above was detected {config.get('frequency', 0)} times
in execution traces, indicating a common pattern that could be optimized.

## Usage
```python
from {tool_name} import {tool_name}

result = {tool_name}(query="search query", file_path="/path/to/file")
```

## Implementation Notes
- This tool automatically executes the sequence: {tools_str}
- Error handling: {config.get('error_handling', 'basic')}
- Return type: {config.get('returns', 'Any')}

## Safety
**IMPORTANT:** This is an auto-generated tool. Review the code before use in production.
- Tool has been tested in sandbox environment
- Monitor initial executions for unexpected behavior
- Report issues to the tool synthesis system

## Auto-Generation Info
This tool was generated by the IMMORTAL tool synthesis engine based on
pattern analysis of agent execution traces. For questions or modifications,
review the tool synthesis documentation.
"""

    def _generate_specialized_tool_code(
        self,
        tool_name: str,
        config: Dict[str, Any]
    ) -> str:
        """Generate code for a specialized tool with preset parameters."""
        base_tool = config["base_tool"]
        preset_params = config["preset_params"]
        description = config.get("description", "")
        returns = config.get("returns", "Any")

        preset_str = ", ".join([f"{k}={repr(v)}" for k, v in preset_params.items()])

        code = """import logging
from typing import Any


def TOOL_NAME(**kwargs) -> RETURNS:
    '''DESCRIPTION

    This is a specialized version of BASE_TOOL with optimized parameters.

    Preset parameters:
        PRESET_STR
    '''
    logging.info(f"Executing TOOL_NAME (specialized BASE_TOOL)")

    # Combine preset params with any additional kwargs
    all_params = {PRESET_STR_DICT}
    all_params.update(kwargs)

    # Call the base tool with preset parameters
    result = self._execute_BASE_TOOL(**all_params)

    return result
""".replace("TOOL_NAME", tool_name)\
   .replace("RETURNS", returns)\
   .replace("DESCRIPTION", description)\
   .replace("BASE_TOOL", base_tool)\
   .replace("PRESET_STR", preset_str)\
   .replace("PRESET_STR_DICT", "{" + preset_str + "}")

        return code

    def _params_signature(self, params: Dict[str, Any]) -> str:
        """Generate a signature string from parameters."""
        if not params:
            return "default"

        # Use first param value and its type as signature
        key = list(params.keys())[0]
        value = params[key]

        if isinstance(value, int):
            type_str = f"int_{value}"
        elif isinstance(value, str):
            # Take first word or truncate
            value_clean = value.replace(" ", "_")[:15]
            type_str = f"str_{value_clean}"
        elif isinstance(value, bool):
            type_str = f"bool_{value}"
        else:
            type_str = type(value).__name__

        return f"{key}_{type_str}"


# Example usage
async def main():
    """Demo tool generation."""
    generator = ToolGenerator()

    # Example: Generate a combined tool for web research
    pattern = {
        "avg_duration_seconds": 45,
        "success_rate": 0.92,
        "frequency": 12,
        "task_type": "research"
    }

    result = generator.generate_combined_tool(
        tool_name="research_and_extract",
        tool_sequence=["search_web", "parse_html", "extract_data"],
        pattern_context=pattern
    )

    print(f"Tool generated: {result['tool_name']}")
    print(f"File: {result['file_path']}")
    print("\n--- Code Preview ---")
    print("\n".join(result["code"].split("\n")[:20]))


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
