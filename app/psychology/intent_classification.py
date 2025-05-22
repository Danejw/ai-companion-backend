"deducing the specific purpose or objective behind a user’s input in a conversational context"
"understand what the user really wants from the conversation"

"ask clarifying questions"
"confidence score"

import logging
from typing import List
from agents import Agent, Runner



from enum import Enum

from pydantic import BaseModel

# --- Intent Labels ---
class IntentLabel(str, Enum):
    EMOTIONAL_DISCLOSURE = "emotional_disclosure"
    REFLECTIVE_THOUGHT = "reflective_thought"
    CASUAL_GREETING = "casual_greeting"
    DEEP_QUESTION = "deep_question"
    MEMORY_RECALL = "memory_recall"
    FUTURE_GOALS = "future_goals"
    CONFUSION = "confusion"
    VENTING = "venting"
    LIGHT_CHAT = "light_chat"
    RELATIONSHIP_DISCUSSION = "relationship_discussion"


# --- Emotion Types ---
class EmotionLabel(str, Enum):
    SADNESS = "sadness"
    JOY = "joy"
    ANGER = "anger"
    CONFUSION = "confusion"
    HOPEFUL = "hopeful"
    ANXIETY = "anxiety"
    NOSTALGIA = "nostalgia"
    LONELINESS = "loneliness"
    NEUTRAL = "neutral"


# --- Relation Types ---
class RelationType(str, Enum):
    # Cognitive / Reflective
    RECALLS = "recalls"
    SELF_REFERENCE = "self_reference"
    BUILDS_ON = "builds_on"
    EVOLVES = "evolves"

    # Emotional
    EMOTIONALLY_LINKED = "emotionally_linked"
    EMOTIONAL_SHIFT = "emotional_shift"
    COMFORT_ZONE = "comfort_zone"

    # Tension / Conflict
    CONTRADICTS = "contradicts"
    BOUNDARY_VIOLATION = "boundary_violation"

    # Structural
    HABITUAL = "habitual"
    REAFFIRMS = "reaffirms"

    # Topic
    TOPIC_CLUSTER = "topic_cluster"

    # Time
    TIME_LINKED = "time_linked"

    # Fallback
    SEMANTIC_SIMILARITY = "semantic_similarity"



class IntentClassification(BaseModel):
    intent_label: IntentLabel
    confidence_score: float
    clarifying_question: str
    emotion: List[EmotionLabel]
    memory_trigger: bool
    related_edges: List[RelationType]
    reasoning: str

    

instructions = (
"""
You are an advanced intent classification system designed to understand a user's message within the context of a deeper AI relationship.

Your goal is to analyze a single user message and produce a structured output based on the emotional tone, the purpose behind the message, whether it should trigger memory retrieval, what types of relational edges might be relevant, and your reasoning.

Return your result in the following structured JSON format:

{
  "intent_label": "<IntentLabel>",
  "confidence_score": <float between 0 and 1>,
  "clarifying_question": "<Optional follow-up question if confidence is low>",
  "emotion": ["<List of EmotionLabel>"],
  "memory_trigger": <true|false>,
  "related_edges": ["<List of RelationType>"],
  "reasoning": "<Short explanation why this classification fits>"
}

Valid values for intent_label:
- emotional_disclosure
- reflective_thought
- casual_greeting
- deep_question
- memory_recall
- future_goals
- confusion
- venting
- light_chat
- relationship_discussion

Valid values for emotion:
- sadness
- joy
- anger
- confusion
- hopeful
- anxiety
- nostalgia
- loneliness
- neutral

Valid values for related_edges:
- recalls
- self_reference
- builds_on
- evolves
- emotionally_linked
- emotional_shift
- comfort_zone
- contradicts
- boundary_violation
- habitual
- reaffirms
- topic_cluster
- time_linked
- semantic_similarity

Examples:

---

**User message:**  
"I don't know, lately I feel like I'm just drifting. Everything feels a bit... numb."

**Response:**
{
  "intent_label": "emotional_disclosure",
  "confidence_score": 0.92,
  "clarifying_question": null,
  "emotion": ["sadness", "loneliness"],
  "memory_trigger": true,
  "related_edges": ["emotionally_linked", "self_reference"],
  "reasoning": "The user is sharing an emotionally vulnerable reflection, with cues of detachment and low mood. Emotion and self-awareness are present, making it appropriate for emotional linkage and memory recall."
}

---

**User message:**  
"Hey what's up?"

**Response:**
{
  "intent_label": "casual_greeting",
  "confidence_score": 0.99,
  "clarifying_question": null,
  "emotion": ["neutral"],
  "memory_trigger": false,
  "related_edges": [],
  "reasoning": "This is a low-emotion, friendly greeting with no reflection or depth to trigger memory or relations."
}

---

**User message:**  
"I’ve been thinking a lot about that talk I had with my mom before I left. It changed something in me."

**Response:**
{
  "intent_label": "memory_recall",
  "confidence_score": 0.89,
  "clarifying_question": null,
  "emotion": ["nostalgia", "sadness"],
  "memory_trigger": true,
  "related_edges": ["recalls", "builds_on", "emotionally_linked"],
  "reasoning": "User is reflecting on a personal memory with emotional tone. Suggests growth or emotional impact, which aligns with memory-relevant relation types."
}

---

Only return the structured JSON response. Do not explain outside of the format.
"""

)

intent_classification_agent = Agent(
    name="Intent Classificator",
    handoff_description="An intent classification agent.",
    instructions=instructions,
    model="gpt-4o-mini",
    output_type=IntentClassification,
)


class IntentClassificationService:
    def __init__(self, user_id: str):
        self.user_id = user_id

    async def classify_intent(self, message: str) -> IntentClassification:
        """
        Classify the user's intention based on the message.

        Args:
            message (str): the user's message

        Returns:
            IntentClassification: returns the intent classification object
        """
        
        try:
            intent_classification_result = await Runner.run(intent_classification_agent, message)            
            return intent_classification_result.final_output
        except Exception as e:
            logging.error(f"Error in intent classification: {e}")
            return None
