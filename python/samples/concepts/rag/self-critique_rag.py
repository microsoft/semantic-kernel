# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureTextEmbedding
from semantic_kernel.connectors.memory.azure_cognitive_search import AzureCognitiveSearchMemoryStore
from semantic_kernel.connectors.memory.azure_cognitive_search.azure_ai_search_settings import AzureAISearchSettings
from semantic_kernel.contents import ChatHistory
from semantic_kernel.core_plugins import TextMemoryPlugin
from semantic_kernel.memory import SemanticTextMemory

COLLECTION_NAME = "generic"


async def populate_memory(memory: SemanticTextMemory) -> None:
    # Add some documents to the ACS semantic memory
    await memory.save_information(COLLECTION_NAME, id="info1", text="My name is Andrea")
    await memory.save_information(COLLECTION_NAME, id="info2", text="I currently work as a tour guide")
    await memory.save_information(COLLECTION_NAME, id="info3", text="I've been living in Seattle since 2005")
    await memory.save_information(
        COLLECTION_NAME,
        id="info4",
        text="I visited France and Italy five times since 2015",
    )
    await memory.save_information(COLLECTION_NAME, id="info5", text="My family is from New York")


async def main() -> None:
    kernel = Kernel()

    azure_ai_search_settings = AzureAISearchSettings()
    vector_size = 1536

    # Setting up OpenAI services for text completion and text embedding
    kernel.add_service(
        AzureChatCompletion(
            service_id="dv",
        ),
    )
    embedding_gen = AzureTextEmbedding(
        service_id="ada",
    )
    kernel.add_service(
        embedding_gen,
    )

    acs_connector = AzureCognitiveSearchMemoryStore(
        vector_size=vector_size,
        search_endpoint=azure_ai_search_settings.endpoint,
        admin_key=azure_ai_search_settings.api_key,
    )

    memory = SemanticTextMemory(storage=acs_connector, embeddings_generator=embedding_gen)
    kernel.add_plugin(TextMemoryPlugin(memory), "TextMemoryPlugin")

    print("Populating memory...")
    await populate_memory(memory)

    "It can give explicit instructions or say 'I don't know' if it does not have an answer."

    sk_prompt_rag = """
Assistant can have a conversation with you about any topic.

Here is some background information about the user that you should use to answer the question below:
{{ recall $user_input }}
User: {{$user_input}}
Assistant: """.strip()
    sk_prompt_rag_sc = """
You will get a question, background information to be used with that question and a answer that was given.
You have to answer Grounded or Ungrounded or Unclear.
Grounded if the answer is based on the background information and clearly answers the question.
Ungrounded if the answer could be true but is not based on the background information.
Unclear if the answer does not answer the question at all.
Question: {{$user_input}}
Background: {{ recall $user_input }}
Answer: {{ $input }}
Remember, just answer Grounded or Ungrounded or Unclear: """.strip()

    user_input = "Do I live in Seattle?"
    print(f"Question: {user_input}")
    req_settings = kernel.get_prompt_execution_settings_from_service_id(service_id="dv")
    chat_func = kernel.add_function(
        function_name="rag", plugin_name="RagPlugin", prompt=sk_prompt_rag, prompt_execution_settings=req_settings
    )
    self_critique_func = kernel.add_function(
        function_name="self_critique_rag",
        plugin_name="RagPlugin",
        prompt=sk_prompt_rag_sc,
        prompt_execution_settings=req_settings,
    )

    chat_history = ChatHistory()
    chat_history.add_user_message(user_input)

    answer = await kernel.invoke(
        chat_func,
        user_input=user_input,
        chat_history=chat_history,
    )
    chat_history.add_assistant_message(str(answer))
    print(f"Answer: {str(answer).strip()}")
    check = await kernel.invoke(self_critique_func, user_input=answer, input=answer, chat_history=chat_history)
    print(f"The answer was {str(check).strip()}")

    print("-" * 50)
    print("   Let's pretend the answer was wrong...")
    print(f"Answer: {str(answer).strip()}")
    check = await kernel.invoke(
        self_critique_func, input=answer, user_input="Yes, you live in New York City.", chat_history=chat_history
    )
    print(f"The answer was {str(check).strip()}")

    print("-" * 50)
    print("   Let's pretend the answer is not related...")
    print(f"Answer: {str(answer).strip()}")
    check = await kernel.invoke(
        self_critique_func, user_input=answer, input="Yes, the earth is not flat.", chat_history=chat_history
    )
    print(f"The answer was {str(check).strip()}")

    await acs_connector.close()


if __name__ == "__main__":
    asyncio.run(main())
