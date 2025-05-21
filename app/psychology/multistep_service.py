from typing import Literal, Optional, List
from pydantic import BaseModel
from agents import Agent, RunResultStreaming, Runner

from app.websockets.context.store import delete_context_key, update_context


class FlowStep(BaseModel):
    content: str

class Flow(BaseModel):
    goal: str
    steps: List[FlowStep]

class MultistepMessage(BaseModel):
    role: str
    content: str
    step_index: Optional[int] = None
    
class MultistepJudgement(BaseModel):
    input: str
    advance: bool
    reason: str
    
class Multistep(BaseModel):
    type: Literal["multistep"]
    goal: Optional[str] = None
    flow_id: Optional[str] = None
    step_index: int
    content: str
    advance: bool = False
    done: bool = False
    reason: str
    previous_steps: List[MultistepMessage] = []

    

judgement_instructions = """
You are a critic and will judge if the user's response is good enough to advance to the next step.

Return exactly this JSON:
{
  "input": str, # what the user said unchanged
  "advance": true|false, # whether to advance to the next step
  "reason": str # why we should advance or not
}
"""
 
multistep_judgement_agent = Agent(
    name="Multistep Judgement Agent",
    instructions=judgement_instructions,
    model="gpt-4o-mini",
    output_type=MultistepJudgement
)




#region Flows
flows: dict[str, Flow] = {
    "cbt-for-anxiety": Flow(
        goal="Reducing Anxiety",
        steps=[
            FlowStep(content="Identify automatic anxious thoughts and cognitive distortions."),
            FlowStep(content="Challenge and restructure distorted thoughts through Socratic questioning."),
            FlowStep(content="Gradually expose the client to avoided situations or fears."),
            FlowStep(content="Teach relaxation techniques (optional) and coping skills."),
            FlowStep(content="Reinforce new behaviors and monitor anxiety levels across exposures."),
        ],
    ),
    "exposure-therapy": Flow(
        goal="Reducing Anxiety",
        steps=[
            FlowStep(content="Create a fear hierarchy (rank fears from least to most intense)."),
            FlowStep(content="Teach relaxation or coping strategies if needed."),
            FlowStep(content="Begin gradual exposure to the least feared item."),
            FlowStep(content="Move up the hierarchy after habituation occurs."),
            FlowStep(content="Process exposure experiences and update beliefs after each step."),
        ],
    ),
    "mindfulness-based-stress-reduction": Flow(
        goal="Reducing Anxiety",
        steps=[
            FlowStep(content="Introduce the concept of mindfulness and nonjudgmental awareness."),
            FlowStep(content="Teach formal practices (breath focus, body scan meditation)." ),
            FlowStep(content="Encourage daily practice and informal mindfulness (mindful eating, walking)." ),
            FlowStep(content="Guide noticing and accepting anxious thoughts without reacting."),
            FlowStep(content="Apply mindfulness in real-world stress or anxiety situations."),
        ],
    ),
    "prolonged-exposure": Flow(
        goal="Processing Trauma",
        steps=[
            FlowStep(content="Psychoeducation about PTSD and rationale for exposure."),
            FlowStep(content="Construct an in vivo exposure hierarchy for trauma reminders."),
            FlowStep(content="Conduct imaginal exposure (recount traumatic event in detail)." ),
            FlowStep(content="Assign homework: listen to exposure recordings and confront avoided situations." ),
            FlowStep(content="Review progress, modify exposures, and consolidate emotional processing." ),
        ],
    ),
    "cognitive-processing-therapy": Flow(
        goal="Processing Trauma",
        steps=[
            FlowStep(content='Explain PTSD and the role of "stuck points" (distorted beliefs).'),
            FlowStep(content="Have the client write a detailed trauma narrative."),
            FlowStep(content="Identify cognitive distortions (e.g., self-blame, guilt)." ),
            FlowStep(content="Use worksheets to challenge and restructure unhelpful beliefs." ),
            FlowStep(content="Reinforce adaptive beliefs and generalize skills to other life areas." ),
        ],
    ),
    "emdr": Flow(
        goal="Processing Trauma",
        steps=[
            FlowStep(content="Identify target traumatic memories and associated beliefs."),
            FlowStep(content="Set up dual attention stimulus (eye movements, tapping, or tones)." ),
            FlowStep(content="Guide client through sets of stimulation while recalling the memory." ),
            FlowStep(content="Pause to process emerging thoughts, images, or emotions."),
            FlowStep(content="Continue until distress reduces, then install positive self-beliefs." ),
        ],
    ),
    "cbt-for-depression": Flow(
        goal="Managing Depression",
        steps=[
            FlowStep(content="Identify negative automatic thoughts and cognitive distortions."),
            FlowStep(content="Challenge and replace distorted thoughts through structured exercises."),
            FlowStep(content="Teach behavioral activation (schedule rewarding activities)." ),
            FlowStep(content="Assign homework: thought records, activity tracking."),
            FlowStep(content="Build relapse prevention strategies by reinforcing core CBT skills."),
        ],
    ),
    "behavioral-activation": Flow(
        goal="Managing Depression",
        steps=[
            FlowStep(content="Assess current behavior patterns and levels of engagement."),
            FlowStep(content="Identify valued activities linked to pleasure or mastery."),
            FlowStep(content="Create an activity schedule with small, achievable goals."),
            FlowStep(content="Monitor mood changes related to activities."),
            FlowStep(content="Problem-solve obstacles and increase activation progressively."),
        ],
    ),
    "interpersonal-psychotherapy": Flow(
        goal="Managing Depression",
        steps=[
            FlowStep(content="Map interpersonal issues contributing to depression (e.g., grief, conflict)."),
            FlowStep(content="Choose one or two key problem areas to target."),
            FlowStep(content="Develop communication and relationship skills around the issue."),
            FlowStep(content="Role-play and practice new interaction patterns."),
            FlowStep(content="Consolidate interpersonal gains and plan for future challenges."),
        ],
    ),
    "mindfulness-based-cognitive-therapy": Flow(
        goal="Managing Depression",
        steps=[
            FlowStep(content="Teach basic mindfulness practices (breath, body, thoughts awareness)." ),
            FlowStep(content="Help clients notice early signs of depressive relapse."),
            FlowStep(content="Train responding mindfully rather than reacting automatically."),
            FlowStep(content="Develop skills for accepting negative emotions without judgment."),
            FlowStep(content="Practice ongoing mindfulness to maintain emotional regulation."),
        ],
    ),
    "emotionally-focused-therapy": Flow(
        goal="Improving Relationships",
        steps=[
            FlowStep(content="Identify negative interaction cycles and underlying attachment fears."),
            FlowStep(content="Access and deepen vulnerable emotional experiences."),
            FlowStep(content="Encourage partners to express attachment needs clearly."),
            FlowStep(content="Facilitate new, supportive emotional responses between partners."),
            FlowStep(content="Consolidate new cycles of positive interaction and secure bonding."),
        ],
    ),
    "behavioral-couples-therapy": Flow(
        goal="Improving Relationships",
        steps=[
            FlowStep(content="Assess relationship satisfaction and problematic behaviors."),
            FlowStep(content="Train communication skills (e.g., active listening, I-statements)." ),
            FlowStep(content="Introduce positive behavior exchanges (increase reinforcement)." ),
            FlowStep(content="Practice problem-solving techniques for conflicts."),
            FlowStep(content="Build maintenance plans for sustaining positive relationship patterns."),
        ],
    ),
    "cbt-for-low-self-esteem": Flow(
        goal="Enhancing Self-Esteem",
        steps=[
            FlowStep(content="Identify core beliefs about self-worth and their origins."),
            FlowStep(content="Challenge global negative self-evaluations using evidence and logic."),
            FlowStep(content="Assign behavioral experiments to test new self-beliefs."),
            FlowStep(content="Build self-affirmation and self-compassion practices."),
            FlowStep(content="Reinforce mastery experiences to consolidate improved self-image."),
        ],
    ),
    "compassion-focused-therapy": Flow(
        goal="Enhancing Self-Esteem",
        steps=[
            FlowStep(content="Psychoeducation on emotion systems (threat, drive, soothe)." ),
            FlowStep(content="Develop compassionate imagery (create a compassionate self)." ),
            FlowStep(content="Practice soothing techniques (e.g., rhythm breathing)." ),
            FlowStep(content="Engage in exercises fostering self-kindness over self-criticism."),
            FlowStep(content="Apply compassion skills to difficult memories and daily self-talk."),
        ],
    ),
    "complicated-grief-therapy": Flow(
        goal="Coping with Grief and Loss",
        steps=[
            FlowStep(content="Provide psychoeducation about complicated grief."),
            FlowStep(content="Guide imaginal revisiting exercises of the death event."),
            FlowStep(content="Encourage situational exposures to reminders avoided after loss."),
            FlowStep(content="Identify and restructure problematic grief-related beliefs."),
            FlowStep(content="Support reconnection to meaningful life goals and relationships."),
        ],
    ),
    "grief-focused-cbt": Flow(
        goal="Coping with Grief and Loss",
        steps=[
            FlowStep(content="Identify unhelpful grief-related thoughts and avoidance patterns."),
            FlowStep(content="Conduct imaginal exposure to painful loss memories."),
            FlowStep(content="Challenge distorted beliefs about guilt, self-blame, or future hopelessness."),
            FlowStep(content="Develop a narrative that honors the lost loved one and affirms life."),
            FlowStep(content="Rebuild life engagement through goal setting and reactivation."),
        ],
    ),
}
#endregion

class MultistepService:
    def __init__(self, user_id: str = ""):
        self.agent = multistep_judgement_agent
        self.multistep : Optional[Multistep] = None
        self.user_id = user_id
        
    def get_flow(self, flow_id: str) -> Flow:
        if flow_id in flows:
            return flows[flow_id]
        else:
            raise ValueError(f"Flow {flow_id} not found")

    def start(self, goal: Optional[str] = None, flow_id: Optional[str] = None) -> Multistep:
        
        if flow_id is not None:
            flow = self.get_flow(flow_id)
            
            if goal is None:
                goal = flow.goal
        
        previous_steps = []
        if flow_id is not None:
            previous_steps = [MultistepMessage(role="assistant", content=f"Starting {flow_id}.")]
        else: 
            if goal is not None:
                previous_steps = [MultistepMessage(role="assistant", content=f"Starting with goal: {goal}.")]
        
        self.multistep = Multistep(
            type="multistep",
            goal=goal,
            flow_id=flow_id,
            step_index=0,
            content=flow.steps[0].content,
            reason=f"Starting {flow_id}.",
            previous_steps=previous_steps
        )

        update_context(self.user_id, "multistep", self.multistep)
        
        print(f"Multistep started: {self.multistep}")
        return self.multistep

    def update_prompt(self) -> str:
        if self.multistep.flow_id is not None:
            purpose = f"""
We're in step {self.multistep.step_index} of flow {self.multistep.flow_id}, 
whose goal is: "{self.multistep.goal}"."""
        else:
            purpose = f"We're starting with goal {self.multistep.goal}, "

        prompt = f"""
{purpose}
 
We asked "{self.multistep.content}"

The user just replied: "{self.multistep.previous_steps[-1].content}".
"""
        return prompt

    async def judge(self, user_input: str) -> MultistepJudgement:
        if self.multistep is None:
            raise ValueError("Multistep flow not started.")

        # Prepare context for the agent
        flow = self.get_flow(self.multistep.flow_id)
        current_step_index = self.multistep.step_index
        step_content = flow.steps[current_step_index].content

        prompt = f"""
        We are currently in the {self.multistep.flow_id} flow, on step {current_step_index } of {len(flow.steps)} steps.
        
        The previous messages are:
        {self.multistep.previous_steps} 
        
        The user reponsed to "{step_content}" with:
        
        "{user_input}"
        
        Should we advance to the next step or drill deeper?
        """

        response: RunResultStreaming = await Runner.run(self.agent, prompt)
        
        judgement = response.final_output

        # Update the multistep state based on judgement
        self.multistep.advance = judgement.advance
        self.multistep.reason = judgement.reason
        self.multistep.previous_steps.append(MultistepMessage(role="user", content=user_input))

        self.advance(judgement)

        print(f"Multistep judged: {self.multistep}")
        return self.multistep

    def advance(self, judgement: MultistepJudgement) -> Multistep:
        if judgement.advance:
            self.multistep.step_index += 1
        
        if self.multistep.flow_id:
            flow = self.get_flow(self.multistep.flow_id)
            if self.multistep.step_index < len(flow.steps):
                self.multistep.content = flow.steps[self.multistep.step_index].content
            else:
                self.finish()
        
        self.update_prompt()
        
        update_context(self.user_id, "multistep", self.multistep)
        
        print(f"Multistep advanced: {self.multistep}")
        return self.multistep

    def abort(self) -> Multistep:
        self.multistep.done = True
        self.multistep.content = f"Flow {self.multistep.flow_id} aborted."
        
        #update_context(self.user_id, "multistep", self.multistep)
        delete_context_key(self.user_id, "multistep")
        
        print(f"Multistep aborted: {self.multistep}")
        return self.multistep

    def finish(self) -> Multistep:
        self.multistep.done = True
        self.multistep.content = f"Flow {self.multistep.flow_id} completed."
        
        update_context(self.user_id, "multistep", self.multistep)
        
        print(f"Multistep finished: {self.multistep}")
        # TODO: DO other things like extract knowledge from the flow
        return self.multistep


