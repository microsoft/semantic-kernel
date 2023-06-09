# Semantic Kernel Feature Matrix by Language

**Legend**

    ✅ - Feature implemented
    🔄 - Feature partially implemented (see associated Note column)
    ❌ - Feature not implemented

## AI Services

|                                   |  C#  | Python | Java | Notes |
|-----------------------------------|:----:|:------:|:----:|-------|
| Text Generation                   | ✅   | ✅     | ✅   | Example: text-davinci-003        |
| Text Embeddings                   | ✅   | ✅     | ✅   | Example: text-embeddings-ada-002 |
| Chat Completion                   | ✅   | ✅     | ❌   | Example: GPT-4, GPT-3.5-turbo    |
| Image Generation                  | ✅   | ❌     | ❌   | Example: Dall-E 2                |

## AI Service Endpoints

|                                   | C#  | Python | Java | Notes |
|-----------------------------------|:---:|:------:|:----:|-------|
| OpenAI                            | ✅  | ✅     | ✅   |                                                               |
| Azure OpenAI                      | ✅  | ✅     | ✅   |                                                               |
| Hugging Face Inference API        | 🔄  | ❌     | ❌   | Coming soon to Python, not all scenarios are covered for .NET |
| Hugging Face Local                | ❌  | ✅     | ❌   |                                                               |
| Custom                            | ✅  | 🔄     | ❌   | Requires to define the service schema in the application      |

## Tokenizers

|                                   | C#  | Python | Java | Notes |
|-----------------------------------|:---:|:------:|:----:|-------|
| GPT2                              | ✅  | ✅     | ✅   |       |
| GPT3                              | ✅  | ❌     | ❌   |       |
| tiktoken                          | ❌  | ❌     | ❌   | Coming soon. Can be added manually to Python via `pip install tiktoken` |

## Core Skills

|                                   | C#  | Python | Java | Notes |
|-----------------------------------|:---:|:------:|:----:|-------|
| TextMemory Skill                  | ✅  | ✅     | 🔄   |       |
| ConversationSummary Skill         | ✅  | ✅     | ❌   |       |
| FileIO Skill                      | ✅  | ✅     | ❌   |       |
| Http Skill                        | ✅  | ✅     | ❌   |       |
| Math Skill                        | ✅  | ✅     | ❌   |       |
| Text Skill                        | ✅  | ✅     | 🔄   |       |
| Time Skill                        | ✅  | ✅     | 🔄   |       |
| Wait Skill                        | ✅  | ❌     | ❌   |       |

## Planning

|                                   | C#  | Python | Java | Notes |
|-----------------------------------|:---:|:------:|:----:|-------|
| Plan                              | ✅  | 🔄     | ❌   | Plan object model to be completed |
| BasicPlanner                      | ❌  | ✅     | ❌   |                                   |
| ActionPlanner                     | ✅  | ❌     | ❌   |                                   |
| SequentialPlanner                 | ✅  | ❌     | ❌   |                                   |

## Memory Connectors, Vector storage

|               | C#  | Python | Java | Notes |
|---------------|:---:|:------:|:----:|-------|
| Azure Search  | ✅  | 🔄     | ❌   | Azure Cognitive Search under development, currently in private preview          |
| Qdrant        | ✅  | ❌     | ❌   |                                                                                 |
| Pinecone      | ✅  | ❌     | ❌   |                                                                                 |
| Weaviate      | ✅  | ✅     | ❌   | Currently supported on Python 3.9-3.11, 3.8 coming soon                         |
| ChromaDb      | ❌  | ✅     | ❌   |                                                                                 |
| Milvus        | ❌  | ❌     | ❌   | Coming soon                                                                     |
| Sqlite        | ✅  | ❌     | ❌   | Vector optimization requires [sqlite-vss](https://github.com/asg017/sqlite-vss) |
| Postgres      | ✅  | ❌     | ❌   | Vector optimization requires [pgvector](https://github.com/pgvector/pgvector)   |
| CosmosDB      | ✅  | ❌     | ❌   | CosmosDB is not optimized for vector storage                                    |

## Connectors and Skill Libraries

|                                       | C#  | Python | Java | Notes |
|---------------------------------------|:---:|:------:|:----:|-------|
| MsGraph                               | ✅  | ❌     | ❌   | Contains connectors for OneDrive, Outlook, ToDos, and Organization Hierarchies  |
| Document and Data Loading Skills      | ✅  | ❌     | ❌   | Pdf, csv, docx, pptx. Currently only supports Word documents                    |
| OpenAPI                               | ✅  | ❌     | ❌   |                                                                                 |
| Web Search Skills (i.e. Bing, Google) | ✅  | ❌     | ❌   |                                                                                 |
| Text Chunkers                         | 🔄  | 🔄     | ❌   |                                                                                 |

# Design Choices

The overall architecture of the core kernel is consistent across all languages,
however, the code follows common paradigms and style of each language.

During the initial development phase, many Python best practices have been ignored
in the interest of velocity and feature parity. The project is now going through
a refactoring exercise to increase code quality.

To make the SDK as lightweight as possible, the core packages have
a minimal set of external dependencies.