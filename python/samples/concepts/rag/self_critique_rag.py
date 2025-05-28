# Copyright (c) Microsoft. All rights reserved.

import asyncio
from dataclasses import dataclass
from textwrap import dedent
from typing import Annotated

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAITextEmbedding
from semantic_kernel.connectors.azure_ai_search import AzureAISearchCollection
from semantic_kernel.contents import ChatHistory
from semantic_kernel.data.vector import VectorStoreField, vectorstoremodel
from semantic_kernel.functions.kernel_function import KernelFunction

"""
This sample shows a really easy way to perform RAG with a vector store.
It creates a simple datamodel, and then creates a collection with that datamodel.
Then we create a function that can search the collection.
Finally, we use the function in a prompt to get an grounding for a answer.
And we then call a function that can check if the answer is grounded or not.
"""


# Define a data model for the collection
# This model will be used to store the information in the collection
@vectorstoremodel(collection_name="generic")
@dataclass
class InfoItem:
    key: Annotated[str, VectorStoreField("key")]
    text: Annotated[str, VectorStoreField("data")]
    embedding: Annotated[
        list[float] | str | None,
        VectorStoreField("vector", dimensions=1536, embedding_generator=OpenAITextEmbedding()),
    ] = None

    def __post_init__(self):
        if self.embedding is None:
            self.embedding = self.text


async def main() -> None:
    kernel = Kernel()

    async with AzureAISearchCollection(record_type=InfoItem) as collection:
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

        print("Creating index for memory...")
        await collection.ensure_collection_deleted()
        await collection.create_collection()

        print("Populating memory...")
        # Add information to the collection
        await collection.upsert([
            InfoItem(key="info1", text="My name is Andrea"),
            InfoItem(key="info2", text="I currently work as a tour guide"),
            InfoItem(key="info3", text="I've been living in Seattle since 2005"),
            InfoItem(key="info4", text="I visited France and Italy five times since 2015"),
            InfoItem(key="info5", text="My family is from New York"),
        ])

        chat_func: KernelFunction = kernel.add_function(  # type: ignore
            function_name="rag",
            plugin_name="RagPlugin",
            prompt=dedent("""
        Assistant can have a conversation with you about any topic.
        It can give explicit instructions or say 'I don't know' if it does not have an answer.

        Here is some background information about the user that you should use to answer the question below:
        Background: {{ memory.recall $question }}
        User: {{$question}}"""),
        )
        self_critique_func: KernelFunction = kernel.add_function(  # type: ignore
            function_name="self_critique_rag",
            plugin_name="RagPlugin",
            prompt=dedent("""
        You will get a question, background information to be used with that question and a answer that was given.
        You have to answer Grounded or Ungrounded or Unclear.
        Grounded if the answer is based on the background information and clearly answers the question.
        Ungrounded if the answer could be true but is not based on the background information.
        Unclear if the answer does not answer the question at all.
        Question: {{$question}}
        Background: {{ memory.recall $question }}
        Answer: {{ $answer_to_question }}
        Remember, just answer Grounded or Ungrounded or Unclear: """),
        )

        print("Asking a question...")
        question = "Do I live in Seattle?"
        print(f"Question: {question}")
        chat_history = ChatHistory()
        chat_history.add_user_message(question)
        answer = await kernel.invoke(
            chat_func,
            question=question,
            chat_history=chat_history,
        )
        chat_history.add_assistant_message(str(answer))
        print(f"Answer: {str(answer).strip()}")
        print("Checking the answer...")
        check = await kernel.invoke(
            self_critique_func,
            question=answer,
            answer_to_question=answer,
            chat_history=chat_history,
        )
        print(f"The answer was {str(check).strip()}")

        print("-" * 50)
        print("   Let's pretend the answer was wrong...")
        wrong_answer = "Yes, you live in New York City."
        print(f"Question: {question}")
        print(f"Answer: {str(wrong_answer).strip()}")
        check = await kernel.invoke(
            self_critique_func,
            question=question,
            answer_to_question=wrong_answer,
            chat_history=chat_history,
        )
        print(f"The answer was {str(check).strip()}")

        print("-" * 50)
        print("   Let's pretend the answer is not related...")
        unrelated_answer = "Yes, the earth is not flat."
        print(f"Question: {question}")
        print(f"Answer: {str(unrelated_answer).strip()}")
        check = await kernel.invoke(
            self_critique_func,
            question=question,
            answer_to_question=unrelated_answer,
            chat_history=chat_history,
        )
        print(f"The answer was {str(check).strip()}")

        print("-" * 50)
        print("Removing collection...")
        await collection.ensure_collection_deleted()


"""
Expected output:
--------------------------------------------------
Creating index for memory...
Populating memory...
Asking a question...
Question: Do I live in Seattle?
Answer: Yes, Andrea, you do live in Seattle.
Checking the answer...
The answer was Grounded
--------------------------------------------------
   Let's pretend the answer was wrong...
Question: Do I live in Seattle?
Answer: Yes, you live in New York City.
The answer was Ungrounded
--------------------------------------------------
   Let's pretend the answer is not related...
Question: Do I live in Seattle?
Answer: Yes, the earth is not flat.
The answer was Unclear
--------------------------------------------------
Removing collection...
"""


if __name__ == "__main__":
    asyncio.run(main())
