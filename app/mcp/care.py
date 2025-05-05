from agents.mcp import MCPServer

care_mcp = MCPServer(
    name="KnoliaCare",
    params={"url": "http://localhost:8001/sse"}  # Replace with your actual care-server URL
)