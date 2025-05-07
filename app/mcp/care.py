from agents.mcp.server import MCPServerSse

care_mcp = MCPServerSse(
    name="KnoliaCare",
    params={"url": "http://localhost:8002/sse"}  # Replace with your actual care-server URL
)

