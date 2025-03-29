import logging
from typing import List, Optional
from agents import Agent, Runner, function_tool
from pydantic import BaseModel, Field

class TodoItem(BaseModel):
    description: str
    status: str
    result: Optional[str] = None

class PlannerOutput(BaseModel):
    plan: str
    todo_list: List[str] = Field(default_factory=list)

class PlannerResult(BaseModel):
    plan: str
    todo_list: List[TodoItem] = Field(default_factory=list)

    def add_todo_item(self, description: str):
        self.todo_list.append(TodoItem(description=description, status="pending"))

    def get_next_pending_item(self) -> Optional[TodoItem]:
        for item in self.todo_list:
            if item.status == "pending":
                return item
        return None

    def mark_item_complete(self, description: str, result: str):
        for item in self.todo_list:
            if item.description == description:
                item.status = "completed"
                item.result = result
                break

class PlannerService:
    """
    A service that encapsulates an AI planner agent which generates actionable plans 
    and dynamic to-do lists based on a user's input.
    """
    def __init__(self):
        instructions = (
            "You are an AI planner tasked with creating a clear, actionable plan based on a user's input. "
            "Create a plan with 3-5 specific, actionable steps that can be executed in sequence. "
            "Each step should be concrete and achievable. "
            "Your output should be a JSON object with two keys: 'plan' (a summary of the plan) and 'todo_list' "
            "(a list of specific, actionable steps)."
        )
        self.agent = Agent(
            name="Planner",
            handoff_description="An agent that generates clear, actionable plans.",
            instructions=instructions,
            model="gpt-4o-mini",
            output_type=PlannerOutput,
            tools=[self.create_plan]
        )

    @function_tool
    async def create_plan(self, task: str) -> PlannerResult:
        """
        Uses the planner agent to create a clear, actionable plan.

        Parameters:
            task (str): The user's task or input that needs to be planned.

        Returns:
            PlannerResult: A Pydantic model containing the plan summary and to-do list with status tracking.
        """
        try:
            result = await Runner.run(self.agent, task)
            # Convert the raw output into our enhanced PlannerResult structure
            planner_result = PlannerResult(
                plan=result.final_output.plan,
                todo_list=[TodoItem(description=item, status="pending") for item in result.final_output.todo_list]
            )
            return planner_result
        except Exception as e:
            logging.error(f"Error creating plan: {e}")
            raise ValueError(f"Failed to create plan: {str(e)}")
