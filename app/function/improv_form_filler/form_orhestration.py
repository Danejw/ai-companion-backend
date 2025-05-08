from typing import Any
from agents import Runner
from app.function.improv_form_filler.form_context import FormContext
from app.function.improv_form_filler.form_agents import extraction_agent, improv_agent

class RequiredField:
    name: str
    type: type


class FormOrchestration:
    def __init__(self, required_fields: list[RequiredField]):
        self.user_id = "user"
        self.required_fields = required_fields
        self.context = FormContext()
        self.missing_fields = required_fields
        self.extraction_agent = extraction_agent
        self.improv_agent = improv_agent

    def get_required_fields(self):
        return self.required_fields

    def get_context(self):
        return self.context

    def get_missing_fields(self):
        return self.missing_fields

    async def extract_data(self, input: str):

        # add the last input in the history key of the context. history is a list of strings
        history = self.context.get_context_key(self.user_id, "history")
        if history is None: history = []
        history.append({"role": "user", "content": input})
        self.context.update_context(self.user_id, "history", history)

        # extraction prompt
        extraction_prompt = f"""
        Currently, we are still missing the following fields: 
        {self.missing_fields}
        """

        self.extraction_agent.instructions += extraction_prompt

        # Extract the data from the input and decide if it fills a missing field
        response = await Runner.run(starting_agent=self.extraction_agent, input=input)
        result = response.final_output

        # if it does not return null and do nothing
        if not result.did_extract:
            return
        else:
            # if it does, fill in the field and remove it from the missing fields
            for extracted_field in result.extracted_fields:
                if extracted_field.name in self.missing_fields:
                    self.context.update_context(self.user_id, extracted_field.name, extracted_field.value)
                    self.missing_fields.remove(extracted_field.name)

        # if there are no missing fields, return True
        if len(self.missing_fields) <= 0:
            self.context.update_context(self.user_id, "did_fill_all_fields", True)
            return {"did_fill_all_fields": True}
        else:
            self.context.update_context(self.user_id, "did_fill_all_fields", False)
            return {"did_fill_all_fields": False}
        
    async def run_improv(self, input: str):
        # get did fill all fields
        did_fill_all_fields = self.context.get_context_key(self.user_id, "did_fill_all_fields")

        prompt = ""
        if did_fill_all_fields is not None and did_fill_all_fields == True:
            prompt = f"""
            You have already filled all the fields. Complete and close out the improv session nicely. 
            """
        else:
            prompt = f""" 
            Continue with the improv session.

            The current history is:
            {self.pretty_print_history()}

            Currently, we are still missing the following fields: 
            {self.missing_fields}
            """

        self.improv_agent.instructions += prompt

        reponse = await Runner.run(starting_agent=self.improv_agent, input=input)
        result = reponse.final_output

        # add the improv to the history
        history = self.context.get_context_key(self.user_id, "history")
        if history is None: history = []
        history.append({"role": "assistant", "content": result})
        self.context.update_context(self.user_id, "history", history)

        return result

    def pretty_print_history(self):
        history = self.context.get_context_key(self.user_id, "history")
        if history is None: history = []
        for message in history:
            print(f"{message['role']}: {message['content']}")


