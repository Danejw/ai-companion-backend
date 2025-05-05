from agents.mcp import MCPServer

connect_mcp = MCPServer(
    name="KnoliaConnect",
    params={"url": "http://localhost:8002/sse"}  # Replace with your actual connect-server URL
)