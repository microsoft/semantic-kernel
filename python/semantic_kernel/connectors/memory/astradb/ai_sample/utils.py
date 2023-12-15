import os

from semantic_kernel.connectors.memory.astradb.ai_sample.utils import *
from semantic_kernel.connectors.memory.astradb import AstraDBMemoryStore
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAITextEmbedding
import semantic_kernel as sk
import openai

OPENAPI_KEY = os.getenv('OPENAPI_KEY')
ASTRADB_APP_TOEKN = os.getenv('ASTRADB_APP_TOEKN')
ASTRADB_ID = os.getenv('ASTRADB_ID')
ASTRADB_REGION = os.getenv('ASTRADB_REGION')
ASTRADB_KEYSPACE = os.getenv('ASTRADB_KEYSPACE')
COLLECTION_NAME = os.getenv('COLLECTION_NAME')


openai.api_key = OPENAPI_KEY

kernel = sk.Kernel()
memory_store = AstraDBMemoryStore(
    ASTRADB_APP_TOEKN, ASTRADB_ID, ASTRADB_REGION, ASTRADB_KEYSPACE, 1536, "cosine")

kernel.add_chat_service(
    "chat-gpt", OpenAIChatCompletion("gpt-3.5-turbo", openai.api_key))
kernel.add_text_embedding_generation_service(
    "ada", OpenAITextEmbedding("text-embedding-ada-002", openai.api_key))

kernel.register_memory_store(memory_store=memory_store)
# kernel.import_skill(sk.core_skills.TextMemorySkill())
