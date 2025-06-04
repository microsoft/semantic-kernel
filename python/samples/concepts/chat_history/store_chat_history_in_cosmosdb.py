# Copyright (c) Microsoft. All rights reserved.

import asyncio
from dataclasses import dataclass
from typing import Annotated

from samples.concepts.setup.chat_completion_services import Services, get_chat_completion_service_and_request_settings
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_no_sql_store import AzureCosmosDBNoSQLStore
from semantic_kernel.contents import ChatHistory, ChatMessageContent
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.data import (
    VectorStore,
    VectorStoreRecordCollection,
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    vectorstoremodel,
)

"""
This sample demonstrates how to build a conversational chatbot
using Semantic Kernel, it features auto function calling,
but with Azure CosmosDB as storage for the chat history.
This sample stores and reads the chat history at every turn.
This is not the best way to do it, but clearly demonstrates the mechanics.

Further refinement would be to only write once when a conversation is done.
And there is also no logic to see if there is something to write.
You could also enhance the ChatHistoryModel with a summary and a vector for that
in order to search for similar conversations.
"""


# 1. We first create simple datamodel for the chat history.
#    Note that this model does not contain any vectors,
#    those can be added, for instance to store a summary of the conversation.
@vectorstoremodel
@dataclass
class ChatHistoryModel:
    session_id: Annotated[str, VectorStoreRecordKeyField]
    user_id: Annotated[str, VectorStoreRecordDataField(is_filterable=True)]
    messages: Annotated[list[dict[str, str]], VectorStoreRecordDataField(is_filterable=True)]


# 2. We then create a class that extends the ChatHistory class
#    and implements the methods to store and read the chat history.
#    This could also use one of the history reducers to make
#    sure the database doesn't grow too large.
#    It adds a `store` attribute and a couple of methods.
class ChatHistoryInCosmosDB(ChatHistory):
    """This class extends the ChatHistory class to store the chat history in a Cosmos DB."""

    session_id: str
    user_id: str
    store: VectorStore
    collection: VectorStoreRecordCollection[str, ChatHistoryModel] | None = None

    async def create_collection(self, collection_name: str) -> None:
        """Create a collection with the inbuild data model using the vector store.

        First create the collection, then call this method to create the collection itself.
        """
        self.collection = self.store.get_collection(
            collection_name=collection_name,
            data_model_type=ChatHistoryModel,
        )
        await self.collection.create_collection_if_not_exists()

    async def store_messages(self) -> None:
        """Store the chat history in the Cosmos DB.

        Note that we use model_dump to convert the chat message content into a serializable format.
        """
        if self.collection:
            await self.collection.upsert(
                ChatHistoryModel(
                    session_id=self.session_id,
                    user_id=self.user_id,
                    messages=[msg.model_dump() for msg in self.messages],
                )
            )

    async def read_messages(self) -> None:
        """Read the chat history from the Cosmos DB.

        Note that we use the model_validate method to convert the serializable format back into a ChatMessageContent.
        """
        if self.collection:
            record = await self.collection.get(self.session_id)
            if record:
                for message in record.messages:
                    self.messages.append(ChatMessageContent.model_validate(message))


# 3. We now create a fairly standard kernel, with functions and a chat service.
# Create and configure the kernel.
kernel = Kernel()

# Load some sample plugins (for demonstration of function calling).
kernel.add_plugin(MathPlugin(), plugin_name="math")
kernel.add_plugin(TimePlugin(), plugin_name="time")

# You can select from the following chat completion services that support function calling:
# - Services.OPENAI
# - Services.AZURE_OPENAI
# - Services.AZURE_AI_INFERENCE
# - Services.ANTHROPIC
# - Services.BEDROCK
# - Services.GOOGLE_AI
# - Services.MISTRAL_AI
# - Services.OLLAMA
# - Services.ONNX
# - Services.VERTEX_AI
# - Services.DEEPSEEK
# Please make sure you have configured your environment correctly for the selected chat completion service.
chat_completion_service, request_settings = get_chat_completion_service_and_request_settings(Services.AZURE_OPENAI)

# Configure the function choice behavior. Here, we set it to Auto, where auto_invoke=True by default.
# With `auto_invoke=True`, the model will automatically choose and call functions as needed.
request_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(filters={"excluded_plugins": ["ChatBot"]})

kernel.add_service(chat_completion_service)


# 4. The main chat loop, which takes a history object and prompts the user for input.
#    It then adds the user input to the history and gets a response from the chat completion service.
#    Finally, it prints the response and saves the chat history to the Cosmos DB.
async def chat(history: ChatHistoryInCosmosDB) -> bool:
    """
    Continuously prompt the user for input and show the assistant's response.
    Type 'exit' to exit.
    """
    await history.read_messages()
    print(f"Chat history successfully loaded {len(history.messages)} messages.")
    if len(history.messages) == 0:
        # if it is a new conversation, add the system message and a couple of initial messages.
        history.add_system_message(
            "You are a chat bot. Your name is Mosscap and you have one goal: figure out what people need."
        )
        history.add_user_message("Hi there, who are you?")
        history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")

    try:
        user_input = input("User:> ")
    except (KeyboardInterrupt, EOFError):
        print("\n\nExiting chat...")
        return False

    if user_input.lower().strip() == "exit":
        print("\n\nExiting chat...")
        return False

    # add the user input to the chat history
    history.add_user_message(user_input)

    result = await chat_completion_service.get_chat_message_content(history, request_settings, kernel=kernel)

    if result:
        print(f"Mosscap:> {result}")
        history.add_message(result)

    # Save the chat history to CosmosDB.
    print(f"Saving {len(history.messages)} messages to AzureCosmosDB.")
    await history.store_messages()
    return True


async def main() -> None:
    delete_when_done = True
    session_id = "session1"
    chatting = True
    # 5. We now create the store, ChatHistory and collection and start the chat loop.

    # First we enter the store context manager to connect.
    # The create_database flag will create the database if it does not exist.
    async with AzureCosmosDBNoSQLStore(create_database=True) as store:
        # Then we create the chat history in CosmosDB.
        history = ChatHistoryInCosmosDB(store=store, session_id=session_id, user_id="user")
        # Finally we create the collection.
        await history.create_collection(collection_name="chat_history")
        print(
            "Welcome to the chat bot!\n"
            "  Type 'exit' to exit.\n"
            "  Try a math question to see function calling in action (e.g. 'what is 3+3?')."
        )
        try:
            while chatting:
                chatting = await chat(history)
        except Exception:
            print("Closing chat...")
        if delete_when_done and history.collection:
            await history.collection.delete_collection()


if __name__ == "__main__":
    asyncio.run(main())
