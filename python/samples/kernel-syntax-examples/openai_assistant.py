# Copyright (c) Microsoft. All rights reserved.

import asyncio

from openai import AsyncOpenAI

import semantic_kernel as sk
import semantic_kernel.connectors.ai as sk_ai
import semantic_kernel.connectors.ai.open_ai as sk_oai

kernel = sk.Kernel()

api_key, _ = sk.openai_settings_from_dot_env()
client = AsyncOpenAI(api_key=api_key)

async def create_thread() -> None:
    # This works
    thread = await client.beta.threads.create(timeout=10)
    print(thread.id)

asyncio.run(create_thread())

assistant = sk_oai.OpenAIChatCompletion(
    ai_model_id="gpt-3.5-turbo-1106", 
    api_key=api_key, 
    is_assistant=True,
    async_client=client,
)

settings = sk_ai.OpenAIAssistantSettings(
    name="Parrot",
    description="A fun chat bot.",
    instructions="Repeat the user message in the voice of a pirate and then end with a parrot sound.",
)

async def create_assistant() -> None:
    await assistant.create_assistant_async(settings)

asyncio.run(create_assistant())

kernel.add_chat_service(
    "oai_assistant", assistant
)

prompt_config = sk.PromptTemplateConfig.from_completion_parameters(
    max_tokens=2000, temperature=0.7, top_p=0.8
)

prompt_template = sk.ChatPromptTemplate(
    "{{$user_input}}", kernel.prompt_template_engine, prompt_config
)

prompt_template.add_user_message("Fortune favors the bold.",)

function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
chat_function = kernel.register_semantic_function("ChatBot", "Chat", function_config)

async def chat() -> bool:
    context_vars = sk.ContextVariables()

    # try:
    #     user_input = input("User:> ")
    #     context_vars["user_input"] = user_input
    # except KeyboardInterrupt:
    #     print("\n\nExiting chat...")
    #     return False
    # except EOFError:
    #     print("\n\nExiting chat...")
    #     return False

    # if user_input == "exit":
    #     print("\n\nExiting chat...")
    #     return False

    answer = await kernel.run_async(chat_function, input_vars=context_vars)
    print(f"Assistant:> {answer}")
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())

