import os
from agents.mcp.server import MCPServerSse

connect_url_dev = os.getenv("CONNECT_URL_DEV")
connect_url_prod = os.getenv("CONNECT_URL_PROD")

if os.getenv("ENV") == "development":
    connect_url = f"{connect_url_dev}/sse"
else:
    connect_url = f"{connect_url_prod}/sse"

connect_mcp = MCPServerSse(
    name="KnoliaConnect",
    params={"url": connect_url}  # Replace with your actual connect-server URL
)


