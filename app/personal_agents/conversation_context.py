# This is a thread-safe container to store conversation history for a single user.
# It also summarizes the conversation every 10 messages.
# This stores the conversation history in local cache memory and is not persistent.

# It is currently NOT being used.
# See the Supabase/conversation_history.py for the persistent version currently in use.

import asyncio
from dataclasses import dataclass, field
import logging
from typing import List, Dict
from agents import Agent, Runner


@dataclass
class ConversationContext:
    """
    A thread-safe container to store conversation history for a single user.
    """
    history: List[str] = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    summarize_every: int = 10

    async def add_message(self, role: str, message: str):
        """
        Appends a new message to the conversation history.
        """
        async with self.lock:
            self.history.append(f"{role}: {message}")
            current_count = len(self.history)
            
        # Check the count outside the lock to avoid deadlock (since summarize() also acquires the lock)
        if current_count >= self.summarize_every:
            await self.summarize()

    async def get_context(self, limit: int = None) -> str:
        """
        Retrieves the full conversation history as a single string.
        """
        async with self.lock:
            # Optionally, you can truncate or summarize if history is too long
            async with self.lock:
                if limit is None:
                    return "\n".join(self.history)
                else:
                    # Get the last 'limit' number of messages
                    recent_messages = self.history[-limit:]
                    return "\n".join(recent_messages)


    async def clear(self):
        """
        Clears the conversation history.
        """
        async with self.lock:
            self.history.clear()
            
    async def summarize(self) -> str:
        """
        Uses an AI agent to summarize the conversation stored in the context.
        Once summarized, clears the context and replaces it only with the summary.

        Returns:
        str: The summary of the conversation.
        """
        # Retrieve the full conversation history.
        full_history = await self.get_context()

        # Define instructions for the summarization agent.
        instructions = (
            "You are an AI that summarizes a conversation. "
            "Read the conversation below and provide a concise summary that captures the key points. "
            "Keep it brief and to the point."
        )

        # Create the summarization agent.
        summarization_agent = Agent(
            name="Summarizer",
            handoff_description="An agent that summarizes conversation context.",
            instructions=instructions,
            model="gpt-4o-mini",
        )

        # Construct the prompt with the conversation history.
        prompt = f"Conversation:\n{full_history}\n\n"
        
        # Run the agent.
        summary_result = await Runner.run(summarization_agent, prompt)
        summary = summary_result.final_output.strip()

        # Clear the existing conversation and store only the summary.
        await self.clear()
        await self.add_message("Summary", summary)

        return summary


# Global in-memory store for conversation contexts keyed by user ID.
# For production in a multi-process scenario, consider a shared store like Redis.
conversation_contexts: Dict[str, ConversationContext] = {}
