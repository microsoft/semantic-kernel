from uuid import uuid4

from semantic_kernel.memory.semantic_text_memory_base import \
    SemanticTextMemoryBase


class CacheBase:
    def __init__(self):
        pass

    async def get_async(self, prompt: str):
        pass

    async def upsert_async(self, prompt: str, completion: str) -> None:
        pass


class NullCache(CacheBase):
    pass


class ExactMatchTextCache(CacheBase):
    def __init__(self):
        self._store = {}

    async def get(self, prompt):
        return self._store.get(prompt)

    async def upsert(self, prompt, completion):
        self._store[prompt] = completion


class SemanticTextCacheBase(CacheBase):
    _collection_name: str
    _storage: SemanticTextMemoryBase
    _similarity_threshold: float

    def set_storage(self, storage: SemanticTextMemoryBase):
        self._storage = storage

    @property
    def storage(self):
        return self._storage
    

class SemanticTextCache(SemanticTextCacheBase):
    _collection_name = "semantic_text_cache"

    def __init__(self, similarity_threshold: float=0.99):
        self._store = {}
        self._similarity_threshold = similarity_threshold
        
    async def get_async(self, prompt: str) -> str:
        # check exact match
        if self._store.get(prompt):
            print("  - SemanticTextCache.get_async: HIT - exact match")
            return self._store[prompt]

        # check semantic match
        try:
            result = await self._storage.search_async(self._collection_name, prompt, 1, self._similarity_threshold)
            completion = result[0].description
            print("  - SemanticTextCache.get_async: HIT - semantic match")
            return completion
        
        except IndexError:
            print("  - SemanticTextCache.get_async: MISS - semantic match")
            return None

    async def upsert_async(self, prompt: str, completion: str) -> None:
        print("  - SemanticTextCache.upsert_async")
        self._store[prompt] = completion

        await self._storage.save_information_async(self._collection_name, prompt, str(uuid4()), completion)
        