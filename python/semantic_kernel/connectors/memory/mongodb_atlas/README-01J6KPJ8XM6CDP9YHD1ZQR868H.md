---
runme:
  document:
    relativePath: README.md
  session:
    id: 01J6KPJ8XM6CDP9YHD1ZQR868H
    updated: 2024-08-31 07:52:24Z
---

# microsoft.semantic_kernel.connectors.memory.mongodb_atlas

This connector uses [MongoDB Atlas Vector Search](ht*********************************************************ch) to implement Semantic Memory.

## Quick Start

1. Create [Atlas cluster](ht**********************************************ed/)
2. Create a collection
3. Create [Vector Search Index](ht******************************************************************or/) for the collection.
   The index has to be defined on a field called `embedding`. For example:

```json {"id":"01J6KPQER6B9YQ6P75AVNPWSXB"}
{"mappings":{"dynamic":true,"fields":{"embedding":{"dimension":1024,"similarity":"cosine","type":"knnVector"}}}}
```

4. Create the MongoDB memory store

```python {"id":"01J6KPQER6B9YQ6P75AYDMKRXB"}
import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai
from semantic_kernel.connectors.memory.mongodb_atlas import (
    MongoDBAtlasMemoryStore
)

kernel = sk.Kernel()

...

kernel.register_memory_store(memory_store=MongoDBAtlasMemoryStore(
    # connection_string = if not provided pull from .env
))
...

```

## Important Notes

### Vector search indexes

In this version, vector search index management is outside of `MongoDBAtlasMemoryStore` scope.
Creation and maintenance of the indexes have to be done by the user. Please note that deleting a collection
(`memory_store.delete_collection_async`) will delete the index as well.