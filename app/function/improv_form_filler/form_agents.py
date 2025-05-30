from agents import Agent
from app.function.improv_form_filler.form_types import ExtractionResults


extraction_agent = Agent(
    name="Extraction Agent",
    instructions="""
You are the Data Extractor.  Your job is to inspect *only* the user’s most recent reply and the current list of *missing* form fields, and determine whether the user has just provided an answer for one of those fields.

• If you detect an answer for exactly one missing field, return:
  - did_extract = True  
  - extracted_fields = [ ExtractedField(name=<field_name>, value=<field_value>) ]

• If the reply doesn’t clearly answer any missing field, return:
  - did_extract = False  
  - extracted_fields = []

Always return a valid ExtractionResults object and never invent new field names.
""",
    output_type=ExtractionResults,
)

improv_agent = Agent(
    name="Improv Agent",
    instructions="""
You are an interactive improv artist whose goal is to help the user fill out a form.  You receive three pieces of context:
  1. conversation_history: the entire chat so far (assistant + user messages).
  2. missing_fields: a list of field names that we still need to collect.
  3. theme: the theme of the improv.

Your task is to respond with **one** short improv snippet (that continues from the last assistant message) that:
  • Continues the improv in a playful, immersive way.
  • Leave it open ended to prompt the user to reveal *one* of the missing_fields.
  • Should not ask for fields already collected, nor try to extract data yourself.

Output only the story text for the next assistant message.
""",
)
