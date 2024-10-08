# Vector Store RAG Demo

This sample demonstrates how to ingest data from a pdf into a vector store and ask questions from an LLM while using RAG to suppliment the LLM with additional information.

## Requirements

### Secret Setup

To run this sample, you need to add some secrets to the secret store for this project.

For Azure OpenAI, you need to add the following secrets:

```cli
dotnet user-secrets set "AIServices:AzureOpenAI:Endpoint" "https://<yourservice>.openai.azure.com"
```

Note that the code doesn't use an API Key to communicate with Azure Open AI, but rather an `AzureCliCredential` so no api key secret is required.

For Azure OpenAI Embeddings, you need to add the following secrets:

```cli
dotnet user-secrets set "AIServices:AzureOpenAIEmbeddings:Endpoint" "https://<yourservice>.openai.azure.com"
```

Note that the code doesn't use an API Key to communicate with Azure Open AI, but rather an `AzureCliCredential` so no api key secret is required.

