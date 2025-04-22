from agents import Agent, ServerSse

# Define the MCP server connection
discord_mcp = ServerSse(url="http://localhost:5000")

# Create the agent with direct MCP server integration
discord_agent = Agent(
    name="Discord",
    handoff_description="A Discord agent for interacting with Discord servers.",
    instructions="""
You are a Discord agent with functions to interact with Discord.

Available Discord Operations:
- Get information about a Discord server using "get_server_info"
- List members in a server using "list_members"
- Create a text channel with "create_text_channel"
- Send messages to channels with "send_message"
- Read recent messages from channels with "read_messages"
- Add emoji reactions to messages with "add_reaction" or "add_multiple_reactions"
- Remove reactions from messages with "remove_reaction"
- Get information about Discord users with "get_user_info"

Always ask for the necessary IDs (server_id, channel_id, message_id) if the user doesn't provide them.
""",
    model="gpt-4o-mini",
    mcp_servers=[discord_mcp]
)
