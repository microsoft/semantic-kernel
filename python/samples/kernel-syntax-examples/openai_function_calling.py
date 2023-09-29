# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.core_skills import MathSkill

system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: figure out what people need.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose. You are also a math wizard, 
especially for adding and subtracting.
You also excel at joke telling, where your tone is often sarcastic.
Once you have the answer I am looking for, 
you will return a full answer to me as soon as possible.
"""

kernel = sk.Kernel()

deployment_name, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
api_version = "2023-07-01-preview"
kernel.add_chat_service(
    "chat-gpt",
    sk_oai.AzureChatCompletion(
        deployment_name,
        endpoint,
        api_key,
        api_version=api_version,
    ),
)

skills_directory = os.path.join(__file__, "../../../../samples/skills")
# adding skills to the kernel
# the joke skill in the FunSkills is a semantic skill and has the function calling disabled.
kernel.import_semantic_skill_from_directory(skills_directory, "FunSkill")
# the math skill is a core skill and has the function calling enabled.
kernel.import_skill(MathSkill(), skill_name="math")

# enabling or disabling function calling is done by setting the function_call parameter for the completion.
# when the function_call parameter is set to "auto" the model will decide which function to use, if any.
# if you only want to use a specific function, set the name of that function in this parameter,
# the format for that is 'SkillName-FunctionName', (i.e. 'math-Add').
# if the model or api version do not support this you will get an error.
prompt_config = sk.PromptTemplateConfig.from_completion_parameters(
    max_tokens=2000,
    temperature=0.7,
    top_p=0.8,
    function_call="auto",
    chat_system_prompt=system_message,
)
prompt_template = sk.ChatPromptTemplate(
    "{{$user_input}}", kernel.prompt_template_engine, prompt_config
)
prompt_template.add_user_message("Hi there, who are you?")
prompt_template.add_assistant_message(
    "I am Mosscap, a chat bot. I'm trying to figure out what people need."
)

function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
chat_function = kernel.register_semantic_function("ChatBot", "Chat", function_config)
# define the functions available
functions = [
    {
        "name": "search_hotels",
        "description": "Retrieves hotels from the search index based on the parameters provided",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location of the hotel (i.e. Seattle, WA)",
                },
                "max_price": {
                    "type": "number",
                    "description": "The maximum price for the hotel",
                },
                "features": {
                    "type": "string",
                    "description": "A comma separated list of features (i.e. beachfront, free wifi, etc.)",
                },
            },
            "required": ["location"],
        },
    }
]


async def main() -> None:
    context = kernel.create_new_context()
    context.variables[
        "user_input"
    ] = "I want to find a hotel in Seattle with free wifi and a pool."

    context = await chat_function.invoke_async(context=context, functions=functions)
    fc_exists, function_call = context.variables.get("function_call")
    if not fc_exists:
        print("No function was called")
        print(f"Output was: {str(context)}")
        return
    function_call = context.variables["function_call"]
    print(f"Function to be called: {function_call.name}")
    print(f"Function parameters: \n{function_call.arguments}")


if __name__ == "__main__":
    asyncio.run(main())
