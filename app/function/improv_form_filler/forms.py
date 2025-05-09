from app.function.improv_form_filler.form_orhestration import ImprovForm, RequiredField


connect_profile_form = ImprovForm(
    name="Connect Profile",
    theme="Romantic Relationship",
    intro="Since you opted into connect, let's begin by getting to know you're preferences better. Lets play a improv, I'll make up a scenerio and you can riff on it.",
    outro="Thanks for playing! Here's what I got from you: ",
    required_fields=[
        RequiredField(name="name", description="The name of the user", type=str),
        RequiredField(name="age", description="The age of the user", type=int),
        RequiredField(name="gender", description="The gender of the user", type=str),
        RequiredField(name="location", description="The location of the user", type=str),
        RequiredField(name="interests", description="The user's personal interests", type=str),
        RequiredField(name="relationship_goals", description="The user's relationship goals", type=str),
        RequiredField(name="values", description="The user's realtionship values", type=str),
        RequiredField(name="fears", description="The user's fears with relationships", type=str),
    ]
)

care_profile_form = ImprovForm(
    name="Care Profile",
    theme="Therapist finder",
    intro="Since you opted into care, let's begin by getting to know you're preferences better. Lets play a improv, I'll make up a scenerio and you can riff on it.",
    outro="Thanks for playing! Here's what I got from you: ",
    required_fields=[
        RequiredField(name="name", description="The name of the user", type=str),
        RequiredField(name="age", description="The age of the user", type=int),
        RequiredField(name="gender", description="The gender of the user", type=str),
        RequiredField(name="location", description="The location of the user", type=str),
        RequiredField(name="care_topics", description="The topics the user would like to discuss", type=str),
        RequiredField(name="care_goals", description="The user's care goals", type=str),
        RequiredField(name="preferred_therapist_gender", description="The user's preferred therapist gender", type=str),
        RequiredField(name="therapist_age", description="The user's preferred therapist age", type=int),
    ]
)