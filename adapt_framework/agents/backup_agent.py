#!/usr/bin/env python3
"""
Backup Agent - Real-world ADAPT Framework Agent

Demonstrates practical use of ADAPT framework for database backup management.
Shows: tool usage, memory persistence, error handling, and reporting.
"""

import sys
sys.path.insert(0, '/adapt/projects/firebird')

from adapt_framework.agents.adapt_agent import ADAPTAgent
from adapt_framework.tools import backup_postgres_database, list_postgres_databases

def main():
    """Run the backup agent."""
    print("🤖 Backup Agent - ADAPT Framework Demo")
    print("PostgreSQL TimescaleDB on port 18030")
    print("=" * 60)

    # Create the backup agent
    agent = ADAPTAgent(
        name="BackupAgent",
        capabilities=["database_management", "backup", "verification"],
        memory_path="/tmp/backup_agent_memory"
    )

    # Register backup tools
    agent.register_tool("list_databases", list_postgres_databases)
    agent.register_tool("backup_database", backup_postgres_database)

    print(f"✅ Agent '{agent.name}' initialized")
    agent.print_status()

    print("\n📋 BACKUP TASK: Backup all user databases")
    print("-" * 60)

    # Start a session
    session_id = agent.start_session("database_backup_run")

    # Step 1: List databases
    print("\n🔍 Step 1: Listing databases...")
    databases = list_postgres_databases()

    if not databases:
        print("❌ No databases found or connection failed")
        return

    print(f"✅ Found {len(databases)} databases:")
    for db in databases:
        print(f"   • {db}")

    # Save this learning
    agent.memory.save_memory(
        session_id,
        "system_info",
        {"database_count": len(databases), "databases": databases},
        importance=0.8
    )

    # Step 2: Backup each database
    print("\n💾 Step 2: Backing up databases...")
    backup_results = []

    for db_name in databases:
        print(f"\n📦 Backing up '{db_name}'...")

        result = agent.executor.execute(
            "backup_database",
            params={"db_name": db_name, "compress": True, "output_path": "/tmp/backups"}
        )

        backup_results.append(result)

        # Record event
        agent.memory.record_event(
            session_id,
            "backup_action",
            f"backup_{db_name}",
            outcome="success" if result.success else "failed",
            success=result.success,
            metadata={
                "database": db_name,
                "file_size_mb": result.output.get("file_size_mb") if result.output else 0,
                "duration": result.execution_time
            } if result.success else {"error": result.error}
        )

        # Learn from result
        if result.success:
            duration = result.output.get("duration_seconds", 0) if result.output else 0
            size_mb = result.output.get("file_size_mb", 0) if result.output else 0

            print(f"   ✅ Success! {size_mb} MB in {duration:.2f}s")
        else:
            print(f"   ❌ Failed: {result.error}")

    # Step 3: Summary
    print("\n📊 Step 3: Backup Summary")
    print("-" * 60)

    successful_backups = sum(1 for r in backup_results if r.success)
    total_size_mb = sum(
        r.output.get("file_size_mb", 0) if r.output else 0
        for r in backup_results if r.success
    )
    total_duration = sum(r.execution_time for r in backup_results)

    print(f"✅ Successful: {successful_backups}/{len(backup_results)}")
    print(f"💾 Total size: {total_size_mb:.2f} MB")
    print(f"⏱️  Total time: {total_duration:.2f}s")

    # Save summary to memory
    agent.memory.save_memory(
        session_id,
        "backup_summary",
        {
            "total_databases": len(databases),
            "successful_backups": successful_backups,
            "total_size_mb": total_size_mb,
            "total_duration_s": total_duration
        },
        importance=0.9
    )

    print("\n" + "=" * 60)
    print("✅ BACKUP AGENT COMPLETED")
    print("=" * 60)

    # Show what we learned
    print("\n🧠 Learnings stored in memory:")
    memories = agent.memory.recall_memory(session_id, limit=5)
    for i, memory in enumerate(memories, 1):
        print(f"   {i}. Type: {memory['type']}")

    return backup_results


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Backup agent interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Backup agent failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
