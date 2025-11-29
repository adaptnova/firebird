"""
ACT - Do things

Core action module for tool execution, action planning, and task management.
Implements the 'ACT' principle from PACK-I.
"""

import asyncio
import time
import inspect
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from dataclasses import dataclass, asdict
import concurrent.futures
import traceback


@dataclass
class ActionResult:
    """Result of an action execution."""

    success: bool
    output: Any
    error: Optional[str]
    execution_time: float
    attempts: int
    tool_name: str
    params: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ActionPlan:
    """Plan for executing a sequence of actions."""

    actions: List[Dict[str, Any]]
    parallel_groups: List[List[int]]
    description: str
    estimated_time: float
    success_criteria: List[str]


class ToolRegistry:
    """
    Registry for managing available tools.
    Provides dynamic tool loading and discovery.
    """

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_info: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, func: Callable, info: Optional[Dict[str, Any]] = None):
        """
        Register a tool.

        Args:
            name: Tool name
            func: Tool function
            info: Optional tool metadata (description, params, etc.)
        """
        self._tools[name] = func

        # Auto-extract info if not provided
        if info is None:
            info = self._extract_tool_info(func)

        self._tool_info[name] = info

    def _extract_tool_info(self, func: Callable) -> Dict[str, Any]:
        """Auto-extract information from a function."""
        sig = inspect.signature(func)

        params = []
        for param_name, param in sig.parameters.items():
            param_info = {
                "name": param_name,
                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                "required": param.default == inspect.Parameter.empty
            }
            params.append(param_info)

        return {
            "name": func.__name__,
            "description": func.__doc__ or "No description",
            "parameters": params,
            "returns": str(sig.return_annotation) if sig.return_annotation != inspect.Signature.empty else "Any"
        }

    def get(self, name: str) -> Optional[Callable]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tool information."""
        return self._tool_info.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def list_tools_with_info(self) -> List[Dict[str, Any]]:
        """List all tools with their information."""
        return [self._tool_info[name] for name in self._tools.keys()]

    def is_available(self, name: str) -> bool:
        """Check if a tool is available."""
        return name in self._tools

    def unregister(self, name: str):
        """Unregister a tool."""
        self._tools.pop(name, None)
        self._tool_info.pop(name, None)


class ActionExecutor:
    """
    Executes actions (tools) with error handling, retries, and timeouts.
    Tracks execution statistics for the KNOW module.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        knowledge_manager: Optional[Any] = None,
        default_timeout: int = 60,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize action executor.

        Args:
            registry: Tool registry
            knowledge_manager: Optional knowledge manager for tracking
            default_timeout: Default timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries (exponential backoff)
        """
        self.registry = registry
        self.knowledge = knowledge_manager
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def execute(
        self,
        tool_name: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        retry_count: Optional[int] = None
    ) -> ActionResult:
        """
        Execute a tool with error handling and retries.

        Args:
            tool_name: Name of the tool to execute
            params: Parameters to pass to the tool
            timeout: Timeout in seconds (uses default if None)
            retry_count: Override max retries for this execution

        Returns:
            ActionResult with execution details
        """
        if params is None:
            params = {}

        if timeout is None:
            timeout = self.default_timeout

        if retry_count is None:
            retry_count = self.max_retries

        attempts = 0
        start_time = time.time()
        last_error = None

        while attempts < retry_count:
            attempts += 1
            attempt_start = time.time()

            try:
                # Get the tool
                tool = self.registry.get(tool_name)
                if tool is None:
                    return ActionResult(
                        success=False,
                        output=None,
                        error=f"Tool '{tool_name}' not found",
                        execution_time=time.time() - start_time,
                        attempts=attempts,
                        tool_name=tool_name,
                        params=params
                    )

                # Execute with timeout
                if asyncio.iscoroutinefunction(tool):  # Handle async functions
                    result = asyncio.run(self._execute_async(tool, params, timeout))
                else:
                    result = self._execute_sync(tool, params, timeout)

                execution_time = time.time() - start_time

                # Success! Track statistics
                if self.knowledge:
                    self.knowledge.update_tool_stats(tool_name, True, execution_time)

                return ActionResult(
                    success=True,
                    output=result,
                    error=None,
                    execution_time=execution_time,
                    attempts=attempts,
                    tool_name=tool_name,
                    params=params
                )

            except Exception as e:
                execution_time = time.time() - attempt_start
                last_error = str(e)

                # Log error with full traceback for debugging
                error_details = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

                # Track failure in knowledge manager
                if self.knowledge:
                    self.knowledge.update_tool_stats(tool_name, False, execution_time)

                # If not the last attempt, log and retry
                if attempts < retry_count:
                    delay = self.retry_delay * (2 ** (attempts - 1))
                    time.sleep(delay)
                    continue

        # All retries exhausted
        return ActionResult(
            success=False,
            output=None,
            error=last_error,
            execution_time=time.time() - start_time,
            attempts=attempts,
            tool_name=tool_name,
            params=params
        )

    async def _execute_async(self, tool: Callable, params: Dict[str, Any], timeout: int) -> Any:
        """Execute an async function with timeout."""
        return await asyncio.wait_for(
            tool(**params) if params else tool(),
            timeout=timeout
        )

    def _execute_sync(self, tool: Callable, params: Dict[str, Any], timeout: int) -> Any:
        """Execute a sync function with timeout using thread pool."""
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(tool, **params) if params else executor.submit(tool)
            return future.result(timeout=timeout)

    def execute_batch(
        self,
        actions: List[Dict[str, Any]],
        continue_on_error: bool = True
    ) -> List[ActionResult]:
        """
        Execute a batch of actions sequentially.

        Args:
            actions: List of action dictionaries with 'tool' and 'params'
            continue_on_error: Whether to continue after errors

        Returns:
            List of ActionResult objects
        """
        results = []

        for action in actions:
            tool_name = action.get("tool")
            params = action.get("params", {})

            result = self.execute(tool_name, params)
            results.append(result)

            if not result.success and not continue_on_error:
                break

        return results

    def execute_parallel(
        self,
        actions: List[Dict[str, Any]],
        max_workers: int = 5
    ) -> List[ActionResult]:
        """
        Execute actions in parallel.

        Args:
            actions: List of action dictionaries
            max_workers: Maximum number of parallel workers

        Returns:
            List of ActionResult objects (order not guaranteed)
        """
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_action = {}
            for i, action in enumerate(actions):
                tool_name = action.get("tool")
                params = action.get("params", {})

                # Wrap in a function that captures all needed data
                def execute_with_context(tool=tool_name, p=params, idx=i):
                    return idx, self.execute(tool, p)

                future = executor.submit(execute_with_context)
                future_to_action[future] = i

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_action):
                try:
                    idx, result = future.result()
                    results.append((idx, result))
                except Exception as e:
                    results.append((future_to_action[future], ActionResult(
                        success=False,
                        output=None,
                        error=str(e),
                        execution_time=0,
                        attempts=0,
                        tool_name="parallel_executor",
                        params={}
                    )))

        # Sort by original index
        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]


class ActionPlanner:
    """
    Plans action sequences based on objectives and available tools.
    Creates optimized execution plans with parallelization where possible.
    """

    def __init__(self, registry: ToolRegistry, knowledge_manager: Optional[Any] = None):
        """
        Initialize action planner.

        Args:
            registry: Tool registry
            knowledge_manager: Optional knowledge manager for tool insights
        """
        self.registry = registry
        self.knowledge = knowledge_manager

    def create_plan(
        self,
        objective: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> ActionPlan:
        """
        Create an execution plan for an objective.

        Args:
            objective: High-level objective
            constraints: Optional constraints (time, resources, etc.)

        Returns:
            ActionPlan with steps and parallelization
        """
        if constraints is None:
            constraints = {}

        # This is a simplified planner - in practice, you'd use an LLM
        # to break down the objective into actionable steps

        # Basic planning heuristics based on objective keywords
        actions = []
        parallel_groups = []

        if "analyze" in objective.lower():
            actions.append({
                "tool": "file_read",
                "params": {"path": "/path/to/analyze"}
            })

        if "implement" in objective.lower() or "build" in objective.lower():
            # Code usually happens in sequence
            actions.append({
                "tool": "code_generate",
                "params": {"prompt": objective}
            })
            actions.append({
                "tool": "file_write",
                "params": {"path": "/output/file.py"}
            })

        if "test" in objective.lower():
            actions.append({
                "tool": "test_run",
                "params": {},
                "depends_on": len(actions) - 1
            })

        # If no plan can be created, return a simple research action
        if not actions:
            actions.append({
                "tool": "research",
                "params": {"query": objective}
            })

        # For now, mark independent actions as parallelizable
        # In a real implementation, analyze dependencies
        if len(actions) > 1:
            parallel_groups = [[0]] if len(actions) > 0 else []

        estimated_time = len(actions) * 10  # 10 seconds per action estimate

        return ActionPlan(
            actions=actions,
            parallel_groups=parallel_groups,
            description=f"Plan for: {objective}",
            estimated_time=estimated_time,
            success_criteria=["All actions completed successfully"]
        )

    def optimize_plan(self, plan: ActionPlan) -> ActionPlan:
        """Optimize an action plan for parallel execution."""
        # Analyze dependencies and group independent actions
        # This is a placeholder - real implementation would analyze
        # actual dependencies between actions

        return plan

    def validate_plan(self, plan: ActionPlan) -> Tuple[bool, List[str]]:
        """
        Validate that a plan can be executed.

        Args:
            plan: ActionPlan to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        for i, action in enumerate(plan.actions):
            tool_name = action.get("tool")

            if not self.registry.is_available(tool_name):
                issues.append(f"Step {i}: Tool '{tool_name}' not available")

            # Check required params
            tool = self.registry.get(tool_name)
            if tool:
                sig = inspect.signature(tool)
                for param_name, param in sig.parameters.items():
                    if param.default == inspect.Parameter.empty:
                        if param_name not in action.get("params", {}):
                            issues.append(f"Step {i}: Missing required param '{param_name}'")

        return len(issues) == 0, issues
