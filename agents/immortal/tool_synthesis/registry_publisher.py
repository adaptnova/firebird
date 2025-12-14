"""Registry Publisher - Publishes validated tools to the global Tool Registry."""

import os
import json
import logging
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional

import nats
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ToolMetadata(BaseModel):
    """Metadata for a tool in the registry."""
    tool_name: str
    version: str
    generated: bool
    generated_at: str
    file_path: str
    synthesizes_tools: List[str]
    success_rate: float
    frequency: int
    category: str
    description: str
    author: str = "IMMORTAL Tool Synthesis Engine"
    safety_reviewed: bool = False
    deployment_approved: bool = False


class RegistryPublisher:
    """Publishes tools to the global registry and notifies agents."""

    def __init__(self, registry_path: str = "core/tool_registry"):
        self.registry_path = registry_path
        self.tools_dir = os.path.join(registry_path, "tools")
        self.metadata_file = os.path.join(registry_path, "registry.json")

        # Create directories
        os.makedirs(self.tools_dir, exist_ok=True)

        # Initialize registry if doesn't exist
        self._initialize_registry()

    def _initialize_registry(self):
        """Create registry.json if it doesn't exist."""
        if not os.path.exists(self.metadata_file):
            initial_registry = {
                "created_at": datetime.utcnow().isoformat(),
                "tool_count": 0,
                "generated_tools_count": 0,
                "categories": {},
                "tools": {}
            }
            with open(self.metadata_file, "w") as f:
                json.dump(initial_registry, f, indent=2)
            logger.info(f"Created new registry at {self.metadata_file}")

    def publish_tool(
        self,
        tool_info: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Publish a tool to the registry.

        Args:
            tool_info: Dictionary with tool code and details
            metadata: Additional metadata about the tool

        Returns:
            Publication result with status
        """
        tool_name = tool_info["tool_name"]
        logger.info(f"Publishing tool: {tool_name}")

        result = {
            "tool_name": tool_name,
            "status": "pending",
            "timestamp": datetime.utcnow().isoformat(),
            "errors": [],
            "warnings": []
        }

        # Step 1: Copy tool file to registry
        try:
            src_path = tool_info["file_path"]
            dst_path = os.path.join(self.tools_dir, f"{tool_name}.py")

            shutil.copy2(src_path, dst_path)
            result["file_path"] = dst_path

        except Exception as e:
            result["errors"].append(f"Failed to copy tool file: {e}")
            result["status"] = "failed"
            return result

        # Step 2: Create __init__.py entry
        try:
            self._update_init_file(tool_name, metadata)
        except Exception as e:
            result["warnings"].append(f"Failed to update __init__.py: {e}")

        # Step 3: Create metadata entry
        try:
            self._update_registry_metadata(tool_name, metadata)
        except Exception as e:
            result["errors"].append(f"Failed to update registry metadata: {e}")
            result["status"] = "failed"
            return result

        # Step 4: Git commit (if in git repo)
        try:
            self._commit_to_git(tool_name, metadata)
        except Exception as e:
            result["warnings"].append(f"Failed to commit to git: {e}")

        result["status"] = "published"
        logger.info(f"Tool {tool_name} published successfully")
        return result

    def _update_init_file(self, tool_name: str, metadata: Dict[str, Any]):
        """Update the __init__.py file in tools directory."""
        init_path = os.path.join(self.tools_dir, "__init__.py")

        # Read existing imports
        existing_imports = []
        if os.path.exists(init_path):
            with open(init_path, "r") as f:
                for line in f:
                    if line.startswith("from ") or line.startswith("import "):
                        existing_imports.append(line.strip())

        # Add new import
        import_line = f"from {tool_name} import {tool_name}"

        if import_line not in existing_imports:
            existing_imports.append(import_line)

            with open(init_path, "w") as f:
                f.write("# Auto-generated tool imports\n")
                for imp in sorted(existing_imports):
                    f.write(imp + "\n")

            logger.info(f"Updated {init_path} with {tool_name}")

    def _update_registry_metadata(self, tool_name: str, metadata: Dict[str, Any]):
        """Update the registry.json metadata file."""
        with open(self.metadata_file, "r") as f:
            registry = json.load(f)

        category = metadata.get("category", "general")

        tool_metadata = ToolMetadata(
            tool_name=tool_name,
            version="1.0.0",
            generated=True,
            generated_at=metadata.get("generated_at", datetime.utcnow().isoformat()),
            file_path=os.path.join(self.tools_dir, f"{tool_name}.py"),
            synthesizes_tools=metadata.get("synthesizes_tools", []),
            success_rate=metadata.get("success_rate", 0),
            frequency=metadata.get("frequency", 1),
            category=category,
            description=metadata.get("description", ""),
            safety_reviewed=metadata.get("safety_reviewed", False),
            deployment_approved=metadata.get("deployment_approved", False)
        )

        registry["tools"][tool_name] = tool_metadata.model_dump()

        # Update category count
        if category not in registry["categories"]:
            registry["categories"][category] = []
        if tool_name not in registry["categories"][category]:
            registry["categories"][category].append(tool_name)

        # Update counts
        registry["tool_count"] = len(registry["tools"])
        registry["generated_tools_count"] = sum(
            1 for t in registry["tools"].values() if t.get("generated", False)
        )

        with open(self.metadata_file, "w") as f:
            json.dump(registry, f, indent=2, default=str)

        logger.info(f"Updated registry metadata for {tool_name}")

    def _commit_to_git(self, tool_name: str, metadata: Dict[str, Any]):
        """Commit tool to git with informative message."""
        import subprocess

        # Check if we're in a git repo
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                check=True,
                capture_output=True
            )
        except:
            logger.info("Not in a git repository, skipping git commit")
            return

        # Add files
        subprocess.run(["git", "add", os.path.join(self.tools_dir, f"{tool_name}.py")])
        subprocess.run(["git", "add", os.path.join(self.tools_dir, "__init__.py")])
        subprocess.run(["git", "add", self.metadata_file])

        # Create commit message
        freq = metadata.get("frequency", 0)
        success_rate = metadata.get("success_rate", 0)
        synthesizes = metadata.get("synthesizes_tools", [])

        commit_message = f"""feat(tools): auto-generate {tool_name}

Auto-synthesized tool based on {freq} observed executions
with {success_rate:.1%} success rate.

Combines tools: {', '.join(synthesizes)}

🤖 Generated by IMMORTAL Tool Synthesis Engine"""

        # Commit
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            capture_output=True
        )

        logger.info(f"Committed {tool_name} to git")

    async def broadcast_tool_available(
        self,
        tool_name: str,
        metadata: Dict[str, Any]
    ):
        """Broadcast to all agents that a new tool is available."""
        try:
            # Connect to NATS
            nc = await nats.connect("nats://localhost:18045")

            message = {
                "event": "tool_available",
                "tool_name": tool_name,
                "metadata": metadata,
                "timestamp": datetime.utcnow().isoformat()
            }

            await nc.publish("agent.notifications.tools", json.dumps(message).encode())
            await nc.flush()
            await nc.close()

            logger.info(f"Broadcast tool availability: {tool_name}")

        except Exception as e:
            logger.error(f"Failed to broadcast tool availability: {e}")

    async def notify_agents(
        self,
        tool_name: str,
        metadata: Dict[str, Any],
        notification_type: str = "new_tool"
    ):
        """Send notification to agents via multiple channels."""
        # Channel 1: NATS message bus
        await self.broadcast_tool_available(tool_name, metadata)

        # Channel 2: Slack notification (if configured)
        self._notify_slack(tool_name, metadata, notification_type)

        # Channel 3: Update Grafana dashboard
        self._update_dashboard(tool_name, metadata)

    def _notify_slack(self, tool_name: str, metadata: Dict[str, Any], notification_type: str):
        """Send Slack notification about new tool."""
        try:
            import requests

            slack_webhook = os.environ.get("SLACK_WEBHOOK_URL")
            if not slack_webhook:
                return

            if notification_type == "new_tool":
                message = f"""
🛠️ *New Auto-Generated Tool Available*

*Tool:* `{tool_name}`
*Category:* {metadata.get('category', 'general')}
*Generated:* {metadata.get('generated_at', 'N/A')}
*Success Rate:* {metadata.get('success_rate', 0):.1%}
*Appears in:* {metadata.get('frequency', 0)} executions

This tool was automatically synthesized based on observed patterns.
"""

                payload = {"text": message}
                requests.post(slack_webhook, json=payload)

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

    def _update_dashboard(self, tool_name: str, metadata: Dict[str, Any]):
        """Update Grafana dashboard with new tool info."""
        try:
            # Write tool info to a metrics file that Grafana reads
            metrics_file = "core/tool_registry/tool_metrics.json"

            tool_metrics = {
                "tool_name": tool_name,
                "generated_at": metadata.get("generated_at"),
                "category": metadata.get("category", "general"),
                "timestamp": datetime.utcnow().isoformat()
            }

            # Append to metrics file
            if os.path.exists(metrics_file):
                with open(metrics_file, "r") as f:
                    metrics = json.load(f)
            else:
                metrics = []

            metrics.append(tool_metrics)

            with open(metrics_file, "w") as f:
                json.dump(metrics[-100:], f, indent=2)  # Keep last 100

        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}")

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the tool registry."""
        with open(self.metadata_file, "r") as f:
            registry = json.load(f)

        return {
            "total_tools": registry["tool_count"],
            "generated_tools": registry["generated_tools_count"],
            "categories": len(registry["categories"]),
            "tools_by_category": {
                cat: len(tools) for cat, tools in registry["categories"].items()
            }
        }


# Example usage
async def main():
    """Demo registry publishing."""
    publisher = RegistryPublisher()

    # Example tool info
    tool_info = {
        "tool_name": "test_tool",
        "file_path": "/tmp/test_tool.py"  # Would be actual generated file
    }

    metadata = {
        "generated_at": "2025-12-02T10:00:00",
        "success_rate": 0.92,
        "frequency": 12,
        "category": "research",
        "description": "Test tool for demo",
        "synthesizes_tools": ["search", "parse", "extract"],
        "deployment_approved": False  # Set to True after manual review
    }

    # Create a dummy tool file for demo
    with open("/tmp/test_tool.py", "w") as f:
        f.write("""def test_tool(query: str) -> str:
    return f"Result: {query}"
""")

    result = publisher.publish_tool(tool_info, metadata)
    print(json.dumps(result, indent=2))

    # Get stats
    stats = publisher.get_registry_stats()
    print("\nRegistry Stats:")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    import asyncio
    import json
    asyncio.run(main())
