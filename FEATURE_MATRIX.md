# Kernel Feature Matrix by Language

## AI Services
| Feature | C# | Python | Notes |
|---|---|---|---|                   
| OpenAI                            | ✅ | ✅ | |
| AzureOpenAI                       | ✅ | ✅ | |
| Hugging Face                      | ✅ | ❌ | Coming soon to Python - both native and web endpoint support | 
| Custom                            | ✅ | ❌ | Requires the user to define the service schema in their application |

## Core Skills
| Feature | C# | Python | Notes |
|---|---|---|---|                   
| TextMemorySkill                   | ✅ | ✅ | |
| PlannerSkill                      | ✅ | ❌ | |
| ConversationSummarySkill          | ✅ | ❌ | | 
| FileIOSkill                       | ✅ | ✅ | |
| HttpSkill                         | ✅ | ❌ | |
| MathSkill                         | ✅ | ❌ | |
| TextSkill                         | ✅ | ✅ | |
| TimeSkill                         | ✅ | ✅ | |

## Connectors and Skill Libraries  
| Feature | C# | Python | Notes |
|---|---|---|---|                   
| Qdrant (Memory)                   | ✅ | ❌ | Vector optimized | 
| ChromaDb (Memory)                 | ❌ | ❌ | |
| Milvus (Memory)                   | ❌ | ❌ | Vector optimized |
| Pinecone (Memory)                 | ❌ | ❌ | Vector optimized |
| Weaviate (Memory)                 | ❌ | ❌ | Vector optimized |
| CosmosDB (Memory)                 | ✅ | ❌ | CosmosDB is not optimized for vector storage |
| Sqlite (Memory)                   | ✅ | ❌ | Sqlite is not optimized for vector storage |
| Azure Cognitive Search            | ❌ | ❌ | |
| MsGraph                           | ✅ | ❌ | Contains connectors for OneDrive, Outlook, ToDos, and Organization Hierarchies |
| Document Skills                   | ✅ | ❌ | Currently only supports Word documents |
| OpenAPI                           | ✅ | ❌ | |
| Web Skills                        | ✅ | ❌ | |

# Design Choices

The overall architecture of the core kernel is consistent across Python and C#,
however, the code should follow common paradigms and style of each language.

During the initial development phase, many Python best practices have been ignored
in the interest of velocity and feature parity. The project is now going through
a refactoring exercise to increase code quality.

To make the Kernel as lightweight as possible, the core pip package should have
a minimal set of external dependencies. On the other hand, the SDK should not
reinvent mature solutions already available, unless of major concerns.
