from agents import Runner
from app.function.improv_form_filler.form_context import FormContext
from app.function.improv_form_filler.form_agents import extraction_agent, improv_agent
from app.function.improv_form_filler.form_types import ImprovForm, Message


class FormOrchestration:
    def __init__(self, improv_form: ImprovForm):
        self.user_id = "user"
        self.improv_form = improv_form
        self.context = FormContext()
        self.missing_fields = improv_form.required_fields
        self.extraction_agent = extraction_agent
        self.improv_agent = improv_agent
        self.in_flow = False

    def get_required_fields(self):
        return self.required_fields

    def get_context(self):
        return self.context

    def get_missing_fields(self):
        return self.missing_fields

    def reset(self):
        self.context.clear_context(self.user_id)
        self.missing_fields = self.improv_form.required_fields
        self.in_flow = False

    async def extract_data(self, input: str):

        # add the last input in the history key of the context. history is a list of strings
        history = self.context.get_context_key(self.user_id, "history")
        if history is None: history = []
        history.append(Message(role="user", content=input))
        self.context.update_context(self.user_id, "history", history)

        # extraction prompt
        extraction_prompt = f"""
        Currently, we are still missing the following fields: 
        {self.missing_fields}
        """

        self.extraction_agent.instructions += extraction_prompt

        if input is None:
            input = "hi"

        # Extract the data from the input and decide if it fills a missing field
        response = await Runner.run(starting_agent=self.extraction_agent, input=input)
        result = response.final_output

        # if it does not return null and do nothing
        if not result.did_extract:
            return result
        else:
            # if it does, fill in the field and remove it from the missing fields
            for extracted_field in result.extracted_fields:
                # Get existing extracted fields or initialize empty dict
                current_fields = self.context.get_context_key(self.user_id, "extracted_fields") or {}
                
                # Add new field to the dict
                current_fields[extracted_field.name] = extracted_field.value
                
                # Update context with all extracted fields
                self.context.update_context(
                    user_id=self.user_id,
                    key="extracted_fields",
                    value=current_fields
                )
                
                # Remove the field from missing_fields
                self.missing_fields = [field for field in self.missing_fields if field.name != extracted_field.name]
            
        return result

    async def run_improv(self, input: str):
        if self.missing_fields == []:
            self.in_flow = False
        else:
            self.in_flow = True

        print("In flow: ", self.in_flow)

        # if the history is 1 or less, add the intro
        history: list[Message] = self.context.get_context_key(self.user_id, "history")  

        # if the history is 1 or less, add the intro    
        if len(history) <= 1 and self.improv_form.intro is not None:
            history.append(Message(role="assistant", content=self.improv_form.intro))
            self.context.update_context(self.user_id, "history", history)
            return self.improv_form.intro
        else:
            prompt = ""
            if self.missing_fields == []:
                # get the user's responses
                extracted_fields = self.context.get_context_key(self.user_id, "extracted_fields")

                print("Extracted fields: ", extracted_fields)

                prompt = f"""                
                You have already filled all the fields. Complete and close out the improv session nicely. 

                The current history is:
                {self.pretty_print_history()}

                Then, summarize the user's responses into a short paragraph. (no improv fluff)
                {extracted_fields}
                """

                self.improv_agent.instructions += prompt

                if input is None:
                    input = "hi"

                if self.improv_form.outro is not None:
                    outro = self.improv_form.outro
                else:
                    outro = ""

                reponse = await Runner.run(starting_agent=self.improv_agent, input=input)
                result = f"{outro}\n\n{reponse.final_output}"

            else:
                prompt = f""" 
                The theme is: {self.improv_form.theme}

                Continue with the improv session.

                The current history is:
                {self.pretty_print_history()}

                Currently, we are still missing the following fields: 
                {self.missing_fields}
                """

                self.improv_agent.instructions += prompt

                if input is None:
                    input = "hi"

                reponse = await Runner.run(starting_agent=self.improv_agent, input=input)
                result = reponse.final_output

            # add the improv to the history
            history = self.context.get_context_key(self.user_id, "history")
            if history is None: history = []
            history.append(Message(role="assistant", content=result))
            self.context.update_context(self.user_id, "history", history)

            return result

    def pretty_print_history(self):
        history: list[Message] = self.context.get_context_key(self.user_id, "history")

        message_string = ""
        for message in history:
            message_string += f"{message.role}: {message.content}\n"

        print("Message string: ", message_string)
        return message_string
