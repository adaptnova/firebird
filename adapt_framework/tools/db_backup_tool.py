"""
Database Backup Tool for ADAPT Framework

Real-world tool for backing up PostgreSQL databases.
Integrates with the ADAPT framework to demonstrate practical usage.
"""

import subprocess
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import os


def backup_postgres_database(
    db_name: str,
    output_path: str,
    host: str = "localhost",
    port: int = 18030,  # PostgreSQL TimescaleDB port (not default 5432)
    username: str = "postgres_admin_user",
    password: Optional[str] = None,
    compress: bool = True,
    maintenance_db: Optional[str] = "teamadapt"  # Changed default to None
) -> Dict[str, Any]:
    """
    Backup a PostgreSQL database using pg_dump.

    Args:
        db_name: Database name to backup
        output_path: Path to save the backup file
        host: Database host (default: localhost)
        port: Database port (default: 5432)
        username: Database username (default: postgres)
        password: Database password (optional)
        compress: Whether to compress the backup (default: True)

    Returns:
        Dictionary with success status, backup file path, and metadata
    """
    try:
        # Ensure output directory exists
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Construct filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{db_name}_backup_{timestamp}.sql"
        if compress:
            filename += ".gz"

        full_output_path = output_dir / filename

        # Build pg_dump command
        cmd = [
            "pg_dump",
            "-h", host,
            "-p", str(port),
            "-U", username,
            "-d", db_name,
            "-f", str(full_output_path)
        ]

        if compress:
            cmd.extend(["-Z", "6"])  # Compression level 6

        # Set PGPASSWORD environment variable if password provided
        env = os.environ.copy()
        if password:
            env["PGPASSWORD"] = password

        # Execute backup
        start_time = datetime.datetime.now()
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True
        )
        end_time = datetime.datetime.now()

        duration = (end_time - start_time).total_seconds()

        if result.returncode == 0:
            # Get file size
            file_size = full_output_path.stat().st_size if full_output_path.exists() else 0

            return {
                "success": True,
                "backup_file": str(full_output_path),
                "db_name": db_name,
                "timestamp": timestamp,
                "duration_seconds": duration,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "compressed": compress,
                "error": None
            }
        else:
            return {
                "success": False,
                "backup_file": None,
                "db_name": db_name,
                "timestamp": timestamp,
                "duration_seconds": duration,
                "file_size_bytes": 0,
                "file_size_mb": 0,
                "compressed": compress,
                "error": result.stderr
            }

    except Exception as e:
        return {
            "success": False,
            "backup_file": None,
            "db_name": db_name,
            "timestamp": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
            "duration_seconds": 0,
            "file_size_bytes": 0,
            "file_size_mb": 0,
            "compressed": compress,
            "error": str(e)
        }


def list_postgres_databases(
    host: str = "localhost",
    port: int = 18030,  # PostgreSQL TimescaleDB port (not default 5432)
    username: str = "postgres_admin_user",
    password: Optional[str] = None,
    maintenance_db: str = "teamadapt"
) -> List[str]:
    """
    List all PostgreSQL databases.
    Uses port 18030 for TeamADAPT PostgreSQL+TimescaleDB cluster.

    Args:
        host: Database host
        port: Database port (18030 for TeamADAPT)
        username: Database username
        password: Database password (optional)
        maintenance_db: Database to connect to for queries (default: teamadapt)

    Returns:
        List of database names
    """
    try:
        # Use psql to list databases
        cmd = [
            "psql",
            "-h", host,
            "-p", str(port),
            "-U", username,
            "-d", maintenance_db,  # Connect to a real database first
            "-t",  # Tuples only
            "-c", "SELECT datname FROM pg_database WHERE datistemplate = false;"
        ]

        env = os.environ.copy()
        if password:
            env["PGPASSWORD"] = password

        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            # Parse output
            databases = [
                db.strip() for db in result.stdout.strip().split('\n')
                if db.strip() and db.strip() != "postgres"
            ]
            return databases
        else:
            print(f"Error listing databases: {result.stderr}")
            return []

    except Exception as e:
        print(f"Exception listing databases: {e}")
        return []


def verify_backup(backup_file: str) -> bool:
    """
    Verify a backup file is valid.

    Args:
        backup_file: Path to the backup file

    Returns:
        True if backup appears valid
    """
    try:
        backup_path = Path(backup_file)

        if not backup_path.exists():
            return False

        if backup_path.suffix == ".gz":
            # Try to read first few bytes of gzipped file
            import gzip
            with gzip.open(backup_path, 'rb') as f:
                header = f.read(100)
                return len(header) > 0
        else:
            # Check if SQL file has content
            return backup_path.stat().st_size > 100

    except Exception as e:
        print(f"Error verifying backup: {e}")
        return False


def cleanup_old_backups(
    backup_dir: str,
    db_name: str,
    keep_days: int = 7
) -> Dict[str, Any]:
    """
    Clean up old backup files.

    Args:
        backup_dir: Directory containing backup files
        db_name: Database name (used for filtering)
        keep_days: Number of days to keep backups

    Returns:
        Dictionary with cleanup results
    """
    try:
        backup_path = Path(backup_dir)
        if not backup_path.exists():
            return {
                "success": True,
                "deleted_count": 0,
                "freed_space_mb": 0,
                "error": "Backup directory does not exist"
            }

        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=keep_days)
        deleted_count = 0
        freed_space = 0

        for backup_file in backup_path.glob(f"{db_name}_backup_*.sql*"):
            # Extract timestamp from filename
            try:
                # Format: db_backup_YYYYMMDD_HHMMSS.sql[.gz]
                stem = backup_file.stem
                if backup_file.suffix == ".gz":
                    # Double extension
                    stem = Path(stem).stem

                timestamp_str = stem.split('_')[-2] + '_' + stem.split('_')[-1]
                file_date = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                if file_date < cutoff_date:
                    size = backup_file.stat().st_size
                    backup_file.unlink()
                    deleted_count += 1
                    freed_space += size

            except Exception as e:
                print(f"Error processing {backup_file}: {e}")
                continue

        return {
            "success": True,
            "deleted_count": deleted_count,
            "freed_space_mb": round(freed_space / (1024 * 1024), 2),
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "deleted_count": 0,
            "freed_space_mb": 0,
            "error": str(e)
        }
