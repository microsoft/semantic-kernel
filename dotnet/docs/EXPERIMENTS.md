# Experiments

The following capabilities are marked experimental in the .NET SDK. Once the APIs for these features are stable, the experimental attribute will be removed. In the meantime, these features are subject to change.

You can use the following diagnostic IDs to ignore warnings or errors for a particular experimental feature. For example, to ignore warnings for the embedding services, add `SKEXP0001` to your list of ignored warnings in your .NET project file as well as the ID for the embedding service you want to use. For example:

```xml
<PropertyGroup>
  <NoWarn>SKEXP0001,SKEXP0011</NoWarn>
</PropertyGroup>
```

## Core

- SKEXP0001: Embedding services
- SKEXP0002: Image services
- SKEXP0003: Memory connectors
- SKEXP0004: Kernel Events

## OpenAI and Azure OpenAI services

- SKEXP0010: Azure OpenAI with your data service
- SKEXP0011: OpenAI embedding service
- SKEXP0012: OpenAI image service
- SKEXP0013: OpenAI parameters

## Memory connectors

- SKEXP0020: Hugging Face AI connector
- SKEXP0021: Azure AI Search memory connector
- SKEXP0022: Chroma memory connector
- SKEXP0023: DuckDB memory connector
- SKEXP0024: Kusto memory connector
- SKEXP0025: Milvus memory connector
- SKEXP0026: Qdrant memory connector
- SKEXP0027: Redis memory connector
- SKEXP0028: Sqlite memory connector
- SKEXP0029: Weaviate memory connector
- SKEXP0030: MongoDB memory connector
- SKEXP0031: Pinecone memory connector
- SKEXP0032: Postgres memory connector

## Functions

- SKEXP0040: GRPC functions
- SKEXP0041: Markdown functions

## Out-of-the-box plugins

- SKEXP0050: Core plugins
- SKEXP0051: Document plugins
- SKEXP0052: Memory plugins
- SKEXP0053: Microsoft 365 plugins
- SKEXP0054: Web plugins
- SKEXP0055: Text chunkcer plugin

## Planners

- SKEXP0060: Handlebars planner
- SKEXP0061: OpenAI Stepwise planner

## Experiments

- SKEXP0101: Experiment with Assistants
- SKEXP0102: Experiment with Flow Orchestration
