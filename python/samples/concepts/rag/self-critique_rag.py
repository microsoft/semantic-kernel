# Copyright (c) Microsoft. All rights reserved.

import asyncio
from dataclasses import dataclass
from textwrap import dedent
from typing import Annotated

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
    OpenAIChatPromptExecutionSettings,
    OpenAITextEmbedding,
)
from semantic_kernel.connectors.memory.azure_ai_search import AzureAISearchCollection
from semantic_kernel.contents import ChatHistory
from semantic_kernel.data import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
    vectorstoremodel,
)

"""
This sample shows a really easy way to have RAG with a vector store.
It creates a simple datamodel, and then creates a collection with that datamodel.
Then we create a function that can search the collection.
Finally, in two different ways we call the function to search the collection.
"""


# Define a data model for the collection
# This model will be used to store the information in the collection
@vectorstoremodel(collection_name="generic")
@dataclass
class InfoItem:
    key: Annotated[str, VectorStoreRecordKeyField]
    text: Annotated[str, VectorStoreRecordDataField]
    embedding: Annotated[
        list[float] | str | None,
        VectorStoreRecordVectorField(dimensions=1536, embedding_generator=OpenAITextEmbedding()),
    ] = None

    def __post_init__(self):
        if self.embedding is None:
            self.embedding = self.text


async def main() -> None:
    kernel = Kernel()

    async with AzureAISearchCollection(data_model_type=InfoItem) as collection:
        # Setting up OpenAI services for text completion and text embedding
        kernel.add_service(OpenAIChatCompletion())
        kernel.add_function(
            plugin_name="memory",
            function=collection.create_search_function(
                function_name="recall",
                description="Search the collection for information.",
                string_mapper=lambda x: x.record.text,
            ),
        )

        print("Populating memory...")
        await collection.delete_collection()
        await collection.create_collection()

        # Add information to the collection
        await collection.upsert([
            InfoItem(key="info1", text="My name is Andrea"),
            InfoItem(key="info2", text="I currently work as a tour guide"),
            InfoItem(key="info3", text="I've been living in Seattle since 2005"),
            InfoItem(key="info4", text="I visited France and Italy five times since 2015"),
            InfoItem(key="info5", text="My family is from New York"),
        ])

        "It can give explicit instructions or say 'I don't know' if it does not have an answer."

        sk_prompt_rag = dedent("""
        Assistant can have a conversation with you about any topic.

        Here is some background information about the user that you should use to answer the question below:
        {{ memory.recall $user_input }}
        User: {{$user_input}}
        Assistant: """)

        sk_prompt_rag_sc = dedent("""
        You will get a question, background information to be used with that question and a answer that was given.
        You have to answer Grounded or Ungrounded or Unclear.
        Grounded if the answer is based on the background information and clearly answers the question.
        Ungrounded if the answer could be true but is not based on the background information.
        Unclear if the answer does not answer the question at all.
        Question: {{$user_input}}
        Background: {{ memory.recall $user_input }}
        Answer: {{ $input }}
        Remember, just answer Grounded or Ungrounded or Unclear: """)

        user_input = "Do I live in Seattle?"
        print(f"Question: {user_input}")
        chat_func = kernel.add_function(
            function_name="rag",
            plugin_name="RagPlugin",
            prompt=sk_prompt_rag,
            prompt_execution_settings=OpenAIChatPromptExecutionSettings(),
        )
        self_critique_func = kernel.add_function(
            function_name="self_critique_rag",
            plugin_name="RagPlugin",
            prompt=sk_prompt_rag_sc,
            prompt_execution_settings=OpenAIChatPromptExecutionSettings(),
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
        check = await kernel.invoke(
            self_critique_func,
            user_input=answer,
            input=answer,
            chat_history=chat_history,
        )
        print(f"The answer was {str(check).strip()}")

        print("-" * 50)
        print("   Let's pretend the answer was wrong...")
        print(f"Answer: {str(answer).strip()}")
        check = await kernel.invoke(
            self_critique_func,
            input=answer,
            user_input="Yes, you live in New York City.",
            chat_history=chat_history,
        )
        print(f"The answer was {str(check).strip()}")

        print("-" * 50)
        print("   Let's pretend the answer is not related...")
        print(f"Answer: {str(answer).strip()}")
        check = await kernel.invoke(
            self_critique_func,
            user_input=answer,
            input="Yes, the earth is not flat.",
            chat_history=chat_history,
        )
        print(f"The answer was {str(check).strip()}")


if __name__ == "__main__":
    asyncio.run(main())
