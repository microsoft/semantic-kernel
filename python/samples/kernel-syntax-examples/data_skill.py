# Copyright (c) Microsoft. All rights reserved.

import asyncio
import pandas as pd
import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.core_skills import DataSkill

kernel = sk.Kernel()
api_key, org_id = sk.openai_settings_from_dot_env()
openai_chat_completion = sk_oai.OpenAIChatCompletion("gpt-3.5-turbo", api_key, org_id)
kernel.add_chat_service("chat_service", openai_chat_completion)

async def main() -> None:
    data = {
        "Name": ["Alice", "Bob", "Charlie", "David", "Eve"],
        "Age": [25, 32, 28, 22, 29],
        "City": ["New York", "Los Angeles", "Chicago", "Houston", "Miami"],
        "Salary": [60000, 75000, 52000, 48000, 67000],
    }
    df = pd.DataFrame(data)
   
    

    data_skill = DataSkill(data=df,service=openai_chat_completion)
    context = sk.ContextVariables()
    context["user_input"] = data_skill.get_row_column_names()
    print(context._variables)
    data_skill = kernel.import_skill(data_skill, skill_name="data")
    
    prompt = "How old is Bob and where does Eve live?"
    query_async = data_skill["queryAsync"]
    result = await query_async.invoke_async(prompt)
    print(result)

    """
    prompt_config = sk.PromptTemplateConfig.from_completion_parameters(
        max_tokens=2000, temperature=0.7, top_p=0.8
    )
    prompt_template = sk.ChatPromptTemplate(  # Create the chat prompt template
        "{{$user_input}}", kernel.prompt_template_engine, prompt_config
    )
    prompt_template.add_user_message(prompt)
    function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)

    query_func = kernel.register_semantic_function(None, "Data", function_config)
    result = await kernel.run_async(query_func, input_vars=context)
    print(context._variables)
    """


if __name__ == "__main__":
    asyncio.run(main())