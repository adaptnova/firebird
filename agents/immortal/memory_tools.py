import os
import psycopg2
from langchain_core.tools import tool

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    # Load secrets manually if not already in env (though agent.py will likely handle this)
    # For now, we assume they are loaded into os.environ
    db_url = os.environ.get("POSTGRES_CLUSTER_URLS")
    if not db_url:
        # Fallback to reading the file directly if env var not set
        try:
            with open("/adapt/secrets/db.env") as f:
                for line in f:
                    if line.startswith("POSTGRES_CLUSTER_URLS="):
                        db_url = line.split("=", 1)[1].strip()
                        break
        except Exception as e:
            print(f"Error reading db.env: {e}")
            
    if not db_url:
        raise ValueError("POSTGRES_CLUSTER_URLS not found in environment or db.env")

    # If it's a list of URLs (comma separated), take the first one
    if "," in db_url:
        db_url = db_url.split(",")[0].strip()
        
    return psycopg2.connect(db_url)

def init_db():
    """Initializes the memories table if it doesn't exist."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_memories (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
    finally:
        conn.close()

@tool
def save_memory(content: str) -> str:
    """Saves a piece of information to long-term memory.
    
    Use this tool to remember important facts, user preferences, or context 
    that should be preserved across different sessions.
    
    Args:
        content: The text content to remember.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO agent_memories (content) VALUES (%s)", (content,))
        conn.commit()
        cur.close()
        return f"Successfully saved to memory: {content}"
    except Exception as e:
        return f"Failed to save memory: {e}"
    finally:
        conn.close()

@tool
def recall_memory(query: str) -> str:
    """Recalls information from long-term memory based on a keyword search.
    
    Use this tool to retrieve past information, user preferences, or context.
    
    Args:
        query: The keyword or phrase to search for.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # Simple ILIKE search for now
        cur.execute("SELECT content, created_at FROM agent_memories WHERE content ILIKE %s ORDER BY created_at DESC LIMIT 5", (f"%{query}%",))
        rows = cur.fetchall()
        cur.close()
        
        if not rows:
            return "No relevant memories found."
            
        results = []
        for row in rows:
            results.append(f"[{row[1]}] {row[0]}")
            
        return "\n".join(results)
    except Exception as e:
        return f"Failed to recall memory: {e}"
    finally:
        conn.close()
