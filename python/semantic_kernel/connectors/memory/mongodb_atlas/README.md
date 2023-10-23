# microsoft.semantic_kernel.connectors.memory.mongodb_atlas

This connector uses [MongoDB Atlas Vector Search](https://www.mongodb.com/products/platform/atlas-vector-search) to implement Semantic Memory.

## Quick Start

1. Create [Atlas cluster](https://www.mongodb.com/docs/atlas/getting-started/)

2. Create a collection

3. Create [Vector Search Index](https://www.mongodb.com/docs/atlas/atlas-search/field-types/knn-vector/) for the collection.
The index has to be defined on a field called ```embedding```. For example:
```
{
  "mappings": {
    "dynamic": true,
    "fields": {
      "embedding": {
        "dimension": 1024,
        "similarity": "cosine",
        "type": "knnVector"
      }
    }
  }
}
```

4. Create the MongoDB memory store
```python
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
In this version, vector search index management is outside of ```MongoDBAtlasMemoryStore``` scope.
Creation and maintenance of the indexes have to be done by the user. Please note that deleting a collection
(```memory_store.delete_collection_async```) will delete the index as well.