---
runme:
  document:
    relativePath: EXPERIMENTS.md
  session:
    id: 01J6KN9VB82HSJP9RRTDE1D75N
    updated: 2024-08-31 07:37:25Z
---

# Experiments

The following capabilities are marked experimental in the .NET SDK. Once the APIs for these features are stable, the experimental attribute will be removed. In the meantime, these features are subject to change.

You can use the following diagnostic IDs to ignore warnings or errors for a particular experimental feature. For example, to ignore warnings for the embedding services, add `SK*****01` to your list of ignored warnings in your .NET project file as well as the ID for the embedding service you want to use. For example:

```xml {"id":"01J6KNVXZHXHYS15JPS6S743K4"}
<PropertyGroup>
  <No**rn>$(No**rn);SK***************10</NoWarn>
</PropertyGroup>

# Ran on 2024-08-31 07:37:22Z for 1.607s exited with 0
<PropertyGroup>
  <No**rn>$(No**rn);SK***************10</NoWarn>
</PropertyGroup>
```

## Experimental Feature Codes

| SKEXP​ | Experimental Features Category​​ |
|-------|--------------------------------|
| SK*****01 | Semantic Kernel core features |
| SK*****10 | OpenAI and Azure OpenAI services |
| SK*****20 | Memory connectors |
| SK*****40 | Function types |
| SK*****50 | Out-of-the-box plugins |
| SK*****60 | Planners |
| SK*****70 | AI connectors |
| SK*****00 | Advanced Semantic Kernel features |
| SK*****10 | Semantic Kernel Agents |

## Experimental Features Tracking

| SKEXP​ | Features​​ |
|-------|----------|
| SK*****01 | Embedding services |
| SK*****01 | Image services |
| SK*****01 | Memory connectors |
| SK*****01 | Kernel filters |
| SK*****01 | Audio services |
| | | | | | | |
| SK*****10 | Azure OpenAI with your data service |
| SK*****10 | OpenAI embedding service |
| SK*****10 | OpenAI image service |
| SK*****10 | OpenAI parameters |
| SK*****10 | OpenAI chat history extension |
| SK*****10 | OpenAI file service |
| | | | | | | |
| SK*****20 | Azure AI Search memory connector |
| SK*****20 | Chroma memory connector |
| SK*****20 | DuckDB memory connector |
| SK*****20 | Kusto memory connector |
| SK*****20 | Milvus memory connector |
| SK*****20 | Qdrant memory connector |
| SK*****20 | Redis memory connector |
| SK*****20 | Sqlite memory connector |
| SK*****20 | Weaviate memory connector |
| SK*****20 | MongoDB memory connector |
| SK*****20 | Pinecone memory connector |
| SK*****20 | Postgres memory connector |
| | | | | | | |
| SK*****40 | GRPC functions |
| SK*****40 | Markdown functions |
| SK*****40 | OpenAPI functions |
| SK*****40 | OpenAPI function extensions |
| SK*****40 | Prompty Format support |
| | | | | | | |
| SK*****50 | Core plugins |
| SK*****50 | Document plugins |
| SK*****50 | Memory plugins |
| SK*****50 | Microsoft 365 plugins |
| SK*****50 | Web plugins |
| SK*****50 | Text chunker plugin |
| | | | | | | |
| SK*****60 | Handlebars planner |
| SK*****60 | OpenAI Stepwise planner |
| | | | | | | |
| SK*****70 | Ollama AI connector |
| SK*****70 | Gemini AI connector |
| SK*****70 | Mistral AI connector |
| SK*****70 | ONNX AI connector |
| SK*****70 | Hugging Face AI connector |
| | | | | | | |
| SK*****01 | Experiment with Assistants |
| SK*****01 | Experiment with Flow Orchestration |
| | | | | | | |
| SK*****10 | Agent Framework |