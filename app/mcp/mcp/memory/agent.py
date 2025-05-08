from agents import Agent
from .server import mcp


memory_mcp = mcp

memory_agent = Agent(
    name="Memory Agent",
    handoff_description="A tool that can be used to add, delete, and search for nodes in the knowledge graph.",
    instructions="You are a helpful assistant that can be used to add, delete, and search for nodes in the knowledge graph. Given the user's input extract the knowledge into the graph.",
    mcp_servers=[memory_mcp]
)
