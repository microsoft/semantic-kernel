# Experiments

The following capabilities are marked experimental in the .NET SDK. Once the APIs for these features are stable, the experimental attribute will be removed. In the meantime, these features are subject to change.

You can use the following diagnostic IDs to ignore warnings or errors for a particular experimental feature. For example, to ignore warnings for the embedding services, add `SKEXP0001` to your list of ignored warnings in your .NET project file as well as the ID for the embedding service you want to use. For example:

```xml
<PropertyGroup>
  <NoWarn>$(NoWarn);SKEXP0001,SKEXP0010</NoWarn>
</PropertyGroup>
```

## Experimental Feature Codes

| SKEXP​ | Experimental Features Category​​ |
|-------|--------------------------------|
| SKEXP0001 | Semantic Kernel core features |
| SKEXP0010 | OpenAI and Azure OpenAI services |
| SKEXP0020 | Memory connectors |
| SKEXP0040 | Function types |
| SKEXP0050 | Out-of-the-box plugins |
| SKEXP0060 | Planners |
| SKEXP0070 | AI connectors |
| SKEXP0080 | Processes |
| SKEXP0100 | Advanced Semantic Kernel features |
| SKEXP0110 | Semantic Kernel Agents |
| SKEXP0120 | Native-AOT |
| MEVD9000 | Microsoft.Extensions.VectorData experimental user-facing APIs |
| MEVD9001 | Microsoft.Extensions.VectorData experimental connector-facing APIs |

## Experimental Features Tracking

| SKEXP​ | Features​​ |
|-------|----------|
| SKEXP0001 | Embedding services |
| SKEXP0001 | Image services |
| SKEXP0001 | Memory connectors |
| SKEXP0001 | Kernel filters |
| SKEXP0001 | Audio services |
| | | | | | | |
| SKEXP0010 | Azure OpenAI with your data service |
| SKEXP0010 | OpenAI embedding service |
| SKEXP0010 | OpenAI image service |
| SKEXP0010 | OpenAI parameters |
| SKEXP0010 | OpenAI chat history extension |
| SKEXP0010 | OpenAI file service |
| | | | | | | |
| SKEXP0020 | Azure AI Search memory connector |
| SKEXP0020 | Chroma memory connector |
| SKEXP0020 | DuckDB memory connector |
| SKEXP0020 | Kusto memory connector |
| SKEXP0020 | Milvus memory connector |
| SKEXP0020 | Qdrant memory connector |
| SKEXP0020 | Redis memory connector |
| SKEXP0020 | Sqlite memory connector |
| SKEXP0020 | Weaviate memory connector |
| SKEXP0020 | MongoDB memory connector |
| SKEXP0020 | Pinecone memory connector |
| SKEXP0020 | Postgres memory connector |
| | | | | | | |
| SKEXP0040 | GRPC functions |
| SKEXP0040 | Markdown functions |
| SKEXP0040 | OpenAPI functions |
| SKEXP0040 | OpenAPI function extensions - API Manifest |
| SKEXP0040 | OpenAPI function extensions - Copilot Agent Plugin |
| SKEXP0040 | Prompty Format support |
| | | | | | | |
| SKEXP0050 | Core plugins |
| SKEXP0050 | Document plugins |
| SKEXP0050 | Memory plugins |
| SKEXP0050 | Microsoft 365 plugins |
| SKEXP0050 | Web plugins |
| SKEXP0050 | Text chunker plugin |
| | | | | | | |
| SKEXP0060 | Handlebars planner |
| SKEXP0060 | OpenAI Stepwise planner |
| | | | | | | |
| SKEXP0070 | Ollama AI connector | | | | | |
| SKEXP0070 | Gemini AI connector | | | | | |
| SKEXP0070 | Mistral AI connector | | | | | |
| SKEXP0070 | ONNX AI connector | | | | | |
| SKEXP0070 | Hugging Face AI connector | | | | | |
| SKEXP0070 | Amazon AI connector | | | | | |
| | | | | | | |
| SKEXP0080 | Process Framework |
| | | | | | | |
| SKEXP0101 | Experiment with Assistants |
| SKEXP0101 | Experiment with Flow Orchestration |
| | | | | | | |
| SKEXP0110 | Agent Framework |
| | | | | | | |
| SKEXP0120 | Native-AOT |
