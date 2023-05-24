# Kernel Feature Matrix by Language

**Legend**

- ✅: Supported
- 🔄: Work in progress
- ❌: Not supported _yet_

## AI Services

| | C# | Python | Java | Notes |
|---|---|---|---|---|
| TextGeneration                    | ✅ | ✅ | ✅ | Example: Text-Davinci-003 |
| TextEmbeddings                    | ✅ | ✅ | ✅ | Example: Text-Embeddings-Ada-002 |
| ChatCompletion                    | ✅ | ✅ | ❌ | Example: GPT4, Chat-GPT |
| Image Generation                  | ✅ | ❌ | ❌ | Example: Dall-E |

## AI Service Endpoints

| | C# | Python | Java| Notes |
|---|---|---|---|---|
| OpenAI                            | ✅ | ✅ | ✅ | |
| AzureOpenAI                       | ✅ | ✅ | ✅ | |
| Hugging Face Inference API        | 🔄 | ❌ | ❌ | Coming soon to Python, not all scenarios are covered for .NET |
| Hugging Face Local                | ❌ | ✅ | ❌ | |
| Custom                            | ✅ | 🔄 | ❌ | Requires the user to define the service schema in their application |

## Tokenizers

| | C# | Python | Java | Notes |
|---|---|---|---|---|
| GPT2                              | ✅ | ✅ | ✅ | |
| GPT3                              | ✅ | ❌ | ❌ | |
| tiktoken                          | 🔄 | ❌ | Coming soon to Python and C#. Can be manually added to Python via `pip install tiktoken` |

## Core Skills

| | C# | Python | Java | Notes |
|---|---|---|---|---|
| TextMemorySkill                   | ✅ | ✅ | 🔄 | |
| ConversationSummarySkill          | ✅ | ✅ | ❌ | |
| FileIOSkill                       | ✅ | ✅ | ❌ | |
| HttpSkill                         | ✅ | ✅ | ❌ | |
| MathSkill                         | ✅ | ✅ | ❌ | |
| TextSkill                         | ✅ | ✅ | 🔄 | |
| TimeSkill                         | ✅ | ✅ | 🔄 | |

## Planning

| | C# | Python | Java | Notes |
|---|---|---|---|---|
| Plan              | ✅ | ❌ | ❌ | |
| SequentialPlanner | ✅ | ❌ | ❌ | |

## Connectors and Skill Libraries

| | C# | Python | Java | Notes |
|---|---|---|---|---|
| Qdrant (Memory)                   | ✅ | ❌ | ❌ | Vector optimized |
| ChromaDb (Memory)                 | ❌ | 🔄 | ❌ | |
| Milvus (Memory)                   | ❌ | ❌ | ❌ | Vector optimized |
| Pinecone (Memory)                 | ✅ | ❌ | ❌ | Vector optimized |
| Weaviate (Memory)                 | ❌ | ❌ | ❌ | Vector optimized |
| CosmosDB (Memory)                 | ✅ | ❌ | ❌ | CosmosDB is not optimized for vector storage |
| Sqlite (Memory)                   | ✅ | ❌ | ❌ | Sqlite is not optimized for vector storage |
| Postgres (Memory)                 | ✅ | ❌ | ❌ | Vector optimized (required the [pgvector](https://github.com/pgvector/pgvector) extension) |
| Azure Cognitive Search            | ❌ | ❌ | ❌ | |
| MsGraph                           | ✅ | ❌ | ❌ | Contains connectors for OneDrive, Outlook, ToDos, and Organization Hierarchies |
| Document Skills                   | ✅ | ❌ | ❌ | Currently only supports Word documents |
| OpenAPI                           | ✅ | ❌ | ❌ | |
| Web Skills                        | ✅ | ❌ | ❌ | |

## Design Choices

The overall architecture of the core kernel is consistent across all languages,
however, the code should follow common paradigms and style of each language.

During the initial development phase, many Python best practices have been ignored
in the interest of velocity and feature parity. The project is now going through
a refactoring exercise to increase code quality.

To make the Kernel as lightweight as possible, the core pip package should have
a minimal set of external dependencies. On the other hand, the SDK should not
reinvent mature solutions already available, unless of major concerns.
