# Python connector extras and optional dependencies

Semantic Kernel keeps the base Python install small while exposing additional providers and stores through
[package extras](pyproject.toml). Install an extra with:

```bash
pip install "semantic-kernel[<extra>]"
```

The version ranges below are copied from `pyproject.toml`. When this table and package metadata disagree,
`pyproject.toml` is authoritative.

## Connectors included in the base install

These public connector surfaces use dependencies already present in the base package and do not require an
additional Semantic Kernel extra.

| Connector / integration | Import path | Extra | Primary package(s) |
| --- | --- | --- | --- |
| OpenAI / Azure OpenAI | `semantic_kernel.connectors.ai.open_ai` | none | `openai >= 2.0.0`, `azure-identity >= 1.13` |
| In-memory vector store | `semantic_kernel.connectors.in_memory` | none | base package |
| Brave search | `semantic_kernel.connectors.brave` | none | `aiohttp ~= 3.8` |
| Google web search | `semantic_kernel.connectors.google_search` | none | `aiohttp ~= 3.8` |
| OpenAPI plugins | `semantic_kernel.connectors.openapi_plugin` | none | `openapi_core >= 0.18,<0.20`, `prance >= 23.6.21,<26.7.20` |
| MCP | `semantic_kernel.connectors.mcp` | none for the current base install | `mcp >= 1.26.0,<2.0` |

## Connector extras

| Extra | Connector / integration | Import path | Optional package constraint(s) |
| --- | --- | --- | --- |
| `anthropic` | Anthropic AI | `semantic_kernel.connectors.ai.anthropic` | `anthropic ~= 0.32` |
| `aws` | Amazon Bedrock | `semantic_kernel.connectors.ai.bedrock` | `boto3 >= 1.36.4,<1.43.0` |
| `azure` | Azure AI Inference, Azure AI Search, Azure Cosmos DB | `semantic_kernel.connectors.ai.azure_ai_inference`, `semantic_kernel.connectors.azure_ai_search`, `semantic_kernel.connectors.azure_cosmos_db` | `azure-ai-inference >= 1.0.0b6`; `azure-core-tracing-opentelemetry >= 1.0.0b11`; `azure-search-documents >= 11.6.0b4,<13.0.0`; `azure-cosmos ~= 4.7` |
| `chroma` | Chroma vector store | `semantic_kernel.connectors.chroma` | `chromadb >= 0.5,<1.6` |
| `faiss` | FAISS vector store | `semantic_kernel.connectors.faiss` | `faiss-cpu >= 1.10.0` |
| `google` | Google AI / Vertex AI | `semantic_kernel.connectors.ai.google` | `google-cloud-aiplatform >= 1.114,<1.134`; `google-genai >= 1.51,<2.21` |
| `hugging_face` | Hugging Face | `semantic_kernel.connectors.ai.hugging_face` | `transformers[torch] >= 5.5.0,<6.0`; `sentence-transformers >= 2.2,<6.0`; `torch == 2.13.0` |
| `milvus` | Milvus vector store | `semantic_kernel.connectors.memory_stores.milvus` | `pymilvus >= 2.3,<2.7`; `milvus >= 2.3,<2.3.8` (non-Windows) |
| `mistralai` | Mistral AI | `semantic_kernel.connectors.ai.mistral_ai` | `mistralai >= 1.2,<2.7.3` |
| `mongo` | MongoDB / MongoDB Atlas vector stores | `semantic_kernel.connectors.mongodb`, `semantic_kernel.connectors.memory_stores.mongodb_atlas` | `pymongo >= 4.8.0,<4.17`; `motor >= 3.3.2,<3.8.0` |
| `ollama` | Ollama | `semantic_kernel.connectors.ai.ollama` | `ollama ~= 0.4` |
| `onnx` | ONNX | `semantic_kernel.connectors.ai.onnx` | Python 3.10: `onnxruntime == 1.22.1`, `onnxruntime-genai == 0.9.0`; Python >3.10: `onnxruntime >= 1.26.0`, `onnxruntime-genai == 0.14.1` |
| `oracledb` | Oracle vector store | `semantic_kernel.connectors.oracle` | `oracledb >= 3.4.1` |
| `pinecone` | Pinecone vector store | `semantic_kernel.connectors.pinecone` | macOS/Linux: `pinecone[asyncio, grpc] ~= 7.0`; Windows: `~= 7.3` |
| `postgres` | PostgreSQL vector store | `semantic_kernel.connectors.postgres` | `psycopg[binary,pool] ~= 3.2` |
| `qdrant` | Qdrant vector store | `semantic_kernel.connectors.qdrant` | `qdrant-client ~= 1.9` |
| `redis` | Redis vector store | `semantic_kernel.connectors.redis` | `redis[hiredis] >= 6,<8`; `types-redis ~= 4.6.0.20240425`; `redisvl ~= 0.4` |
| `sql` | SQL Server vector store | `semantic_kernel.connectors.sql_server` | `pyodbc >= 5.2` |
| `usearch` | USearch vector store | `semantic_kernel.connectors.memory_stores.usearch` | `usearch >= 2.16,<2.25`; `pyarrow >= 12.0,<26.0` |
| `weaviate` | Weaviate vector store | `semantic_kernel.connectors.weaviate` | `weaviate-client >= 4.17.0,<5.0` |

## Other optional extras

These extras are package features rather than a single connector module, but are still part of the public installation
surface and are listed here so the documentation stays in sync with `pyproject.toml`.

| Extra | Purpose | Optional package constraint(s) |
| --- | --- | --- |
| `autogen` | AutoGen compatibility | `autogen-agentchat >= 0.2,<0.4` |
| `copilotstudio` | Copilot Studio integration | `microsoft-agents-copilotstudio-client >= 0.3.1`; `microsoft-agents-activity >= 0.3.1` |
| `mcp` | Explicit MCP extra / compatibility install | `mcp >= 1.8,<2.0` |
| `notebooks` | Notebook development/runtime support | `ipykernel >= 6.29,<8.0` |
| `pandas` | Pandas integration | `pandas ~= 2.2` |
| `realtime` | Realtime audio/websocket support | `websockets >= 13,<16`; `aiortc >= 1.9.0` |

## CI and maintenance

- `python/pyproject.toml` is the source of truth for extra names and version constraints.
- `python/tests/unit/test_connector_extras_documentation.py` verifies that every optional-dependency extra declared in
  `pyproject.toml` is represented in this document.
- Provider-specific unit and integration tests remain responsible for runtime compatibility. This table does not replace
  those tests or guarantee that a third-party service is reachable.
- If an extra is added, renamed, or removed in `pyproject.toml`, update this document in the same pull request.

For local development with every optional dependency, see [DEV_SETUP.md](DEV_SETUP.md) and use
`uv sync --all-extras --dev`.
