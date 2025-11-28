#!/usr/bin/env python3
"""Test all databases - Phase 1: Foundation"""

import asyncio
import sys

async def test_postgresql():
    """Test PostgreSQL"""
    try:
        import asyncpg
        conn = await asyncpg.connect('postgresql://postgres_admin_user:***@localhost:18030/teamadapt')
        result = await conn.fetchval('SELECT 1')
        await conn.close()
        return result == 1
    except Exception as e:
        print(f"❌ PostgreSQL failed: {e}")
        return False

def test_qdrant():
    """Test Qdrant"""
    try:
        import requests
        response = requests.get('http://localhost:18050/health')
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Qdrant failed: {e}")
        return False

def test_mongodb():
    """Test MongoDB"""
    try:
        from pymongo import MongoClient
        client = MongoClient('mongodb://admin:***@localhost:18070/admin')
        result = client.admin.command('ping')
        client.close()
        return True
    except Exception as e:
        print(f"❌ MongoDB failed: {e}")
        return False

async def main():
    print("=" * 60)
    print("DATABASE CONNECTIVITY TEST")
    print("=" * 60)
    
    results = {
        'PostgreSQL': await test_postgresql(),
        'Qdrant': test_qdrant(),
        'MongoDB': test_mongodb(),
    }
    
    print("\n✅ RESULTS:")
    print("-" * 60)
    for db, status in results.items():
        symbol = "✅" if status else "❌"
        print(f"{symbol} {db}: {'OK' if status else 'FAILED'}")
    
    all_ok = all(results.values())
    print("-" * 60)
    if all_ok:
        print("✅ ALL DATABASES OPERATIONAL!")
    else:
        print("❌ Some databases failed")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
