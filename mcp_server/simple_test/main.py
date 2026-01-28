"""Simple MCP Test Server"""
from mcp.server.fastmcp import FastMCP

# Create server with a name that has underscore
server = FastMCP("simple_test")


@server.tool(name="simple_test_search")
async def search_tool(query: str) -> str:
    """A simple search tool"""
    return f"Search results for: {query}"


if __name__ == "__main__":
    server.run()
