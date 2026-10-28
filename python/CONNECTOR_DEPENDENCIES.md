# Python connector dependencies

This page maps the public Python connector import roots to the optional dependency extra that installs their provider SDK. The version constraints below mirror `python/pyproject.toml`; that file is the source of truth when a constraint changes.

Install a connector with the corresponding extra:

```bash
pip install --upgrade "semantic-kernel[google]"
```

If a connector is marked **base**, no connector-specific extra is required. Its dependencies are already part of the default `semantic-kernel` installation. Provider credentials and service endpoints are still required where applicable.

## AI and model connectors

| Connector import root | Extra | Provider packages and constraints |
| --- | --- | --- |
| `semantic_kernel.connectors.ai.open_ai` | **base** | `openai >= 2.0.0` |
| `semantic_kernel.connectors.ai.anthropic` | `anthropic` | `anthropic ~= 0.32` |
| `semantic_kernel.connectors.ai.bedrock` | `aws` | `boto3 >= 1.36.4,<1.43.0` |
| `semantic_kernel.connectors.ai.azure_ai_inference` | `azure` | `azure-ai-inference >= 1.0.0b6`; tracing support uses `azure-core-tracing-opentelemetry >= 1.0.0b11` |
| `semantic_kernel.connectors.ai.google` | `google` | `google-cloud-aiplatform >= 1.114,<1.134`; `google-genai >= 1.51,<1.75` |
| `semantic_kernel.connectors.ai.hugging_face` | `hugging_face` | `transformers[torch] >= 4.28,<6.0`; `sentence-transformers >= 2.2,<6.0`; `torch==2.13.0` |
| `semantic_kernel.connectors.ai.mistral_ai` | `mistralai` | `mistralai >= 1.2,<2.7.3` |
| `semantic_kernel.connectors.ai.nvidia` | **base** | Uses the OpenAI-compatible client already installed by the base package |
| `semantic_kernel.connectors.ai.ollama` | `ollama` | `ollama ~= 0.4` |
| `semantic_kernel.connectors.ai.onnx` | `onnx` | Python 3.10: `onnxruntime==1.22.1`, `onnxruntime-genai==0.9.0`; newer Python: `onnxruntime>=1.26.0`, `onnxruntime-genai==0.14.1` |

The shared embedding interfaces under `semantic_kernel.connectors.ai.embeddings` are **base** APIs. The concrete provider connector determines whether an additional extra is needed.

## Vector stores and memory connectors

| Connector import root | Extra | Provider packages and constraints |
| --- | --- | --- |
| `semantic_kernel.connectors.azure_ai_search` and `semantic_kernel.connectors.memory_stores.azure_cognitive_search` | `azure` | `azure-search-documents >= 11.6.0b4,<13.0.0` |
| `semantic_kernel.connectors.azure_cosmos_db` | `azure`, `mongo` | `azure-cosmos ~= 4.7`; `pymongo >= 4.8.0,<4.17` |
| `semantic_kernel.connectors.chroma` and `semantic_kernel.connectors.memory_stores.chroma` | `chroma` | `chromadb >= 0.5,<1.6` |
| `semantic_kernel.connectors.faiss` | `faiss` | `faiss-cpu >= 1.10.0` |
| `semantic_kernel.connectors.memory_stores.astradb` | **base** | Uses the base HTTP and numerical dependencies; no Astra SDK extra is defined |
| `semantic_kernel.connectors.memory_stores.milvus` | `milvus` | `pymilvus >= 2.3,<2.7`; `milvus >= 2.3,<2.3.8` on non-Windows systems |
| `semantic_kernel.connectors.mongodb` and `semantic_kernel.connectors.memory_stores.mongodb_atlas` | `mongo` | `pymongo >= 4.8.0,<4.17`; `motor >= 3.3.2,<3.8.0` |
| `semantic_kernel.connectors.pinecone` and `semantic_kernel.connectors.memory_stores.pinecone` | `pinecone` | Linux/macOS: `pinecone[asyncio, grpc] ~= 7.0`; Windows: `pinecone[asyncio, grpc] ~= 7.3` |
| `semantic_kernel.connectors.postgres` and `semantic_kernel.connectors.memory_stores.postgres` | `postgres` | `psycopg[binary,pool] ~= 3.2` |
| `semantic_kernel.connectors.qdrant` and `semantic_kernel.connectors.memory_stores.qdrant` | `qdrant` | `qdrant-client ~= 1.9` |
| `semantic_kernel.connectors.redis` and `semantic_kernel.connectors.memory_stores.redis` | `redis` | `redis[hiredis] >= 6,<8`; `types-redis ~= 4.6.0.20240425`; `redisvl ~= 0.4` |
| `semantic_kernel.connectors.memory_stores.usearch` | `usearch` | `usearch >= 2.16,<2.25`; `pyarrow >= 12.0,<24.0` |
| `semantic_kernel.connectors.weaviate` and `semantic_kernel.connectors.memory_stores.weaviate` | `weaviate` | `weaviate-client >= 4.17.0,<5.0` |
| `semantic_kernel.connectors.in_memory` | **base** | Uses base `numpy` and `scipy` dependencies; no provider SDK is required |

## Search, protocol, and utility connectors

| Connector import root | Extra | Provider packages and constraints |
| --- | --- | --- |
| `semantic_kernel.connectors.brave` | **base** | Uses the base HTTP client; configure a Brave Search API key |
| `semantic_kernel.connectors.google_search` | **base** | Uses the base HTTP client; configure Google Custom Search credentials |
| `semantic_kernel.connectors.mcp` | `mcp` | The default install already includes `mcp >= 1.26.0,<2.0`; the extra declares `mcp >= 1.8,<2.0` for explicit connector installation |
| `semantic_kernel.connectors.oracle` | `oracledb` | `oracledb >= 3.4.1` |
| `semantic_kernel.connectors.sql_server` | `sql` | `pyodbc >= 5.2` |

The `semantic_kernel.connectors.memory`, `semantic_kernel.connectors.search`, and `semantic_kernel.connectors.openapi_plugin` modules are facades or protocol helpers. They do not introduce a separate provider SDK; install the extra for the concrete connector they expose.

## Keeping the table current

When adding or changing a connector:

1. Add or update the provider constraint in `python/pyproject.toml`.
2. Update this table with the public import root and extra.
3. Verify the connector's import path and dependency mapping in the same change.

