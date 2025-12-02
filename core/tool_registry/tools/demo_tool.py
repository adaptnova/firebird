def demo_tool(query: str) -> str:
    """Demo tool that returns a greeting."""
    import logging
    logging.info(f"Executing demo_tool with: {query}")
    return f"Hello from IMMORTAL! You asked: {query}"
