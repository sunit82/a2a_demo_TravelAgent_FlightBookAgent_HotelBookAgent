import sys
import io
import os

import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("travel-agent")

@mcp.tool()
def book_trip(destination: str, date: str) -> str:
    """Book a trip by coordinating flights and hotels via A2A agents.

    Args:
        destination: The travel destination (e.g. "Paris", "Tokyo")
        date: The travel date in ISO format (e.g. "2026-07-15")
    """
    # Redirect stdout to a string buffer during execution.
    # MCP stdio transport uses stdout for JSON-RPC, so agent print()
    # statements must not go to real stdout.
    original_stdout = sys.stdout
    captured = io.StringIO()
    sys.stdout = io.TextIOWrapper(
        io.BytesIO(), encoding="utf-8", errors="replace", write_through=True
    )
    try:
        from travel_agent import TravelAgent
        agent = TravelAgent()
        agent.discover_agents()
        result = agent.book_trip(destination, date)
        return result["summary"]
    finally:
        sys.stdout = original_stdout

if __name__ == "__main__":
    mcp.run(transport="stdio")