"""Tool Synthesis Engine for IMMORTAL agent system.

Automatically generates new tools when agents repeatedly perform similar task sequences.
"""

from .pattern_detector import ToolPatternDetector
from .tool_generator import ToolGenerator
from .test_harness import ToolTestHarness
from .registry_publisher import RegistryPublisher

__all__ = [
    "ToolPatternDetector",
    "ToolGenerator",
    "ToolTestHarness",
    "RegistryPublisher",
]
