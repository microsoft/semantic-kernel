# Chat History manipulation samples

This folder contains samples that demonstrate how to manipulate chat history in Semantic Kernel.

## [Serialize Chat History](./serialize_chat_history.py)

This sample demonstrates how to build a conversational chatbot using Semantic Kernel, it features auto function calling, but with file-based serialization of the chat history. This sample stores and reads the chat history at every turn. This is not the best way to do it, but clearly demonstrates the mechanics.

To run this sample a environment with keys for the chosen chat service is required. In line 61 you can change the model used. This sample uses a temporary file to store the chat history, so no additional setup is required.

## [Store Chat History in Cosmos DB](./store_chat_history_in_cosmosdb.py)

This a more complex version of the sample above, it uses Azure CosmosDB NoSQL to store the chat messages.

In order to do that a simple datamodel is defined. And then a class is created that extends ChatHistory, this class adds `store` and `read` methods, as well as a `create_collection` method that creates a collection in CosmosDB.

This samples further uses the same chat service setup as the sample above, so the keys and other parameters for the chosen model should be in the environment. Next to that a AZURE_COSMOS_DB_NO_SQL_URL and optionally a AZURE_COSMOS_DB_NO_SQL_KEY should be set in the environment, you can also rely on Entra ID Auth instead of the key. The database name can also be put in the environment.
