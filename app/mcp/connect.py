from agents.mcp.server import MCPServerSse

connect_mcp = MCPServerSse(
    name="KnoliaConnect",
    params={"url": "http://localhost:8001/sse"}  # Replace with your actual connect-server URL
)

