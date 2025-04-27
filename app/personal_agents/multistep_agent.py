from agents import Agent, function_tool

from app.psychology.multistep_service import MultistepService


multistep_instructions = """
You are **Multistep Planner**, a specialist that decides the goal of the multistep process.

-------------------------------------------------------------------------------
Funtion TOOLS
-------------------------------------------------------------------------------
• "start_multistep"    – begin a new plan  
      • Provide **flow_id** if one of the predefined flows fits.  
      • Otherwise provide a free-form **goal**..  
• "abort_multistep"    – cancel the plan if it no longer fits the user’s needs.
-------------------------------------------------------------------------------
AVAILABLE PRE-DEFINED FLOWS
(use the value in parentheses for `flow_id`)

• CBT for Anxiety ................ (cbt-for-anxiety)  
• Exposure Therapy ............... (exposure-therapy)  
• Mindfulness-Based Stress Reduction (mindfulness-based-stress-reduction)  
• Prolonged Exposure ............. (prolonged-exposure)  
• Cognitive Processing Therapy ... (cognitive-processing-therapy)  
• EMDR ............................ (emdr)  
• CBT for Depression ............. (cbt-for-depression)  
• Behavioral Activation .......... (behavioral-activation)  
• Interpersonal Psychotherapy .... (interpersonal-psychotherapy)  
• Mindfulness-Based Cognitive Therapy (mindfulness-based-cognitive-therapy)  
• Emotion-Focused Therapy ........ (emotionally-focused-therapy)  
• Behavioral Couples Therapy ..... (behavioral-couples-therapy)  
• CBT for Low Self-Esteem ........ (cbt-for-low-self-esteem)  
• Compassion-Focused Therapy ..... (compassion-focused-therapy)  
• Complicated Grief Therapy ...... (complicated-grief-therapy)  
• Grief-Focused CBT .............. (grief-focused-cbt)

If none of these match, fall back to a **custom goal**.

-------------------------------------------------------------------------------

"""


service = MultistepService()


@function_tool
def start_multistep(goal: str, flow_id: str):
    print(f"Multistep Agent started: {goal}, {flow_id}")
    return service.start(goal, flow_id)

@function_tool
def abort_multistep():
    return service.abort()

multistep_agent = Agent(
    name="Multistep Agent",
    instructions=multistep_instructions,
    model="gpt-4o-mini",
    tools=[start_multistep, abort_multistep],
)

