---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: westey-m
date: 2024-06-05
deciders: sergeymenshykh, markwallace, rbarreto, dmytrostruk, westey-m, matthewbolanos, eavanvalkenburg
consulted: stephentoub, dluc, ajcvickers, roji
informed: 
---

# Updated Memory Connector Design

## Context and Problem Statement

Semantic Kernel has a collection of connectors to popular Vector databases e.g. Azure AI Search, Chroma, Milvus, ...
Each Memory connector implements a memory abstraction defined by Semantic Kernel and allows developers to easily integrate Vector databases into their applications.
The current abstractions are experimental and the purpose of this ADR is to progress the design of the abstractions so that they can graduate to non experimental status.

### Problems with current design

1. The `IMemoryStore` interface has four responsibilities with different cardinalities. Some are schema aware and others schema agnostic.
2. The `IMemoryStore` interface only supports a fixed schema for data storage, retrieval and search, which limits its usability by customers with existing data sets.
2. The `IMemoryStore` implementations are opinionated around key encoding / decoding and collection name sanitization, which limits its usability by customers with existing data sets.

Responsibilities:

|Functional Area|Cardinality|Significance to Semantic Kernel|
|-|-|-|
|Collection/Index create|An implementation per store type and model|Valuable when building a store and adding data|
|Collection/Index list names, exists and delete|An implementation per store type|Valuable when building a store and adding data|
|Data Storage and Retrieval|An implementation per store type|Valuable when building a store and adding data|
|Vector Search|An implementation per store type, model and search type|Valuable for many scenarios including RAG, finding contradictory facts based on user input, finding similar memories to merge, etc.|


### Memory Store Today
```cs
interface IMemoryStore
{
    // Collection / Index Management
    Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default);
    IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancellationToken = default);
    Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default);
    Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default);

    // Data Storage and Retrieval
    Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default);
    IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records, CancellationToken cancellationToken = default);
    Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default);
    IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withVectors = false, CancellationToken cancellationToken = default);
    Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default);
    Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default);

    // Vector Search
    IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        ReadOnlyMemory<float> embedding,
        int limit,
        double minRelevanceScore = 0.0,
        bool withVectors = false,
        CancellationToken cancellationToken = default);

    Task<(MemoryRecord, double)?> GetNearestMatchAsync(
        string collectionName,
        ReadOnlyMemory<float> embedding,
        double minRelevanceScore = 0.0,
        bool withEmbedding = false,
        CancellationToken cancellationToken = default);
}
```

### Actions

1. The `IMemoryStore` should be split into different interfaces, so that schema aware and schema agnostic operations are separated.
2. The **Data Storage and Retrieval** and **Vector Search** areas should allow typed access to data and support any schema that is currently available in the customer's data store.
3. The collection / index create functionality should allow developers to use a common definition that is part of the abstraction to create collections.
4. The collection / index list/exists/delete functionality should allow management of any collection regardless of schema.
5. Remove opinionated behaviors from connectors. The opinionated behavior limits the ability of these connectors to be used with pre-existing vector databases. As far as possible these behaviors should be moved into decorators or be injectable.  Examples of opinionated behaviors:
    1. The AzureAISearch connector encodes keys before storing and decodes them after retrieval since keys in Azure AI Search supports a limited set of characters.
    2. The AzureAISearch connector sanitizes collection names before using them, since Azure AI Search supports a limited set of characters.
    3. The Redis connector prepends the collection name on to the front of keys before storing records and also registers the collection name as a prefix for records to be indexed by the index.

### Non-functional requirements for new connectors
1. Ensure all connectors are throwing the same exceptions consistently with data about the request made provided in a consistent manner.
2. Add consistent telemetry for all connectors.
3. As far as possible integration tests should be runnable on build server.

### New Designs

The separation between collection/index management and record management.

```mermaid
---
title: SK Collection/Index and record management
---
classDiagram
    note for IVectorRecordStore "Can manage records for any scenario"
    note for IVectorCollectionCreate "Can create collections and\nindexes"
    note for IVectorCollectionNonSchema "Can retrieve/delete any collections and\nindexes"

    namespace SKAbstractions{
        class IVectorCollectionCreate{
            <<interface>>
            +CreateCollection
        }

        class IVectorCollectionNonSchema{
            <<interface>>
            +GetCollectionNames
            +CollectionExists
            +DeleteCollection
        }

        class IVectorRecordStore~TModel~{
            <<interface>>
            +Upsert(TModel record) string
            +UpserBatch(TModel record) string
            +Get(string key) TModel
            +GetBatch(string[] keys) TModel[]
            +Delete(string key)
            +DeleteBatch(string[] keys)
        }
    }

    namespace AzureAIMemory{
        class AzureAISearchVectorCollectionCreate{
        }

        class AzureAISearchVectorCollectionNonSchema{
        }

        class AzureAISearchVectorRecordStore{
        }
    }

    namespace RedisMemory{
        class RedisVectorCollectionCreate{
        }

        class RedisVectorCollectionNonSchema{
        }

        class RedisVectorRecordStore{
        }
    }

    IVectorCollectionCreate <|-- AzureAISearchVectorCollectionCreate
    IVectorCollectionNonSchema <|-- AzureAISearchVectorCollectionNonSchema
    IVectorRecordStore <|-- AzureAISearchVectorRecordStore

    IVectorCollectionCreate <|-- RedisVectorCollectionCreate
    IVectorCollectionNonSchema <|-- RedisVectorCollectionNonSchema
    IVectorRecordStore <|-- RedisVectorRecordStore
```

How to use your own schema with core sk functionality.

```mermaid
---
title: Chat History Break Glass
---
classDiagram
    note for IVectorRecordStore "Can manage records\nfor any scenario"
    note for IVectorCollectionCreate "Can create collections\nan dindexes"
    note for IVectorCollectionNonSchema "Can retrieve/delete any\ncollections and indexes"
    note for CustomerHistoryVectorCollectionCreate "Creates history collections and indices\nusing Customer requirements"
    note for CustomerHistoryVectorRecordStore "Decorator class for IVectorRecordStore that maps\nbetween the customer model to our model"

    namespace SKAbstractions{
        class IVectorCollectionCreate{
            <<interface>>
            +CreateCollection
        }

        class IVectorCollectionNonSchema{
            <<interface>>
            +GetCollectionNames
            +CollectionExists
            +DeleteCollection
        }

        class IVectorRecordStore~TModel~{
            <<interface>>
            +Upsert(TModel record) string
            +Get(string key) TModel
            +Delete(string key) string
        }

        class ISemanticTextMemory{
            <<interface>>
            +SaveInformationAsync()
            +SaveReferenceAsync()
            +GetAsync()
            +DeleteAsync()
            +SearchAsync()
            +GetCollectionsAsync()
        }
    }

    namespace CustomerProject{
        class CustomerHistoryModel{
            +string text
            +float[] vector
            +Dictionary~string, string~ properties
        }

        class CustomerHistoryVectorCollectionCreate{
            +CreateCollection
        }

        class CustomerHistoryVectorRecordStore{
            -IVectorRecordStore~CustomerHistoryModel~ _store
            +Upsert(ChatHistoryModel record) string
            +Get(string key) ChatHistoryModel
            +Delete(string key) string
        }
    }

    namespace SKCore{
        class SemanticTextMemory{
            -IVectorRecordStore~ChatHistoryModel~ _VectorRecordStore
            -IMemoryCollectionService _collectionsService
            -ITextEmbeddingGenerationService _embeddingGenerationService
        }

        class ChatHistoryPlugin{
            -ISemanticTextMemory memory
        }

        class ChatHistoryModel{
            +string message
            +float[] embedding
            +Dictionary~string, string~ metadata
        }
    }

    IVectorCollectionCreate <|-- CustomerHistoryVectorCollectionCreate

    IVectorRecordStore <|-- CustomerHistoryVectorRecordStore
    IVectorRecordStore <.. CustomerHistoryVectorRecordStore
    CustomerHistoryModel <.. CustomerHistoryVectorRecordStore
    ChatHistoryModel <.. CustomerHistoryVectorRecordStore

    ChatHistoryModel <.. SemanticTextMemory
    IVectorRecordStore <.. SemanticTextMemory
    IVectorCollectionCreate <.. SemanticTextMemory

    ISemanticTextMemory <.. ChatHistoryPlugin
```

### Vector Store Cross Store support - General Features

A comparison of the different ways in which stores implement storage capabilities to help drive decisions:

|Feature|Azure AI Search|Weaviate|Redis|Chroma|FAISS|Pinecone|LLamaIndex|PostgreSql|Qdrant|Milvus|
|-|-|-|-|-|-|-|-|-|-|-|
|Get Item Support|Y|Y|Y|Y||Y||Y|Y|Y|
|Batch Operation Support|Y|Y|Y|Y||Y||||Y|
|Per Item Results for Batch Operations|Y|Y|Y|N||N|||||
|Keys of upserted records|Y|Y|N<sup>3</sup>|N<sup>3</sup>||N<sup>3</sup>||||Y|
|Keys of removed records|Y||N<sup>3</sup>|N||N||||N<sup>3</sup>|
|Retrieval field selection for gets|Y||Y<sup>4<sup>|P<sup>2</sup>||N||Y|Y|Y|
|Include/Exclude Embeddings for gets|P<sup>1</sup>|Y|Y<sup>4,1<sup>|Y||N||P<sup>1</sup>|Y|N|
|Failure reasons when batch partially fails|Y|Y|Y|N||N|||||
|Is Key separate from data|N|Y|Y|Y||Y||N|Y|N|
|Can Generate Ids|N|Y|N|N||Y||Y|N|Y|
|Can Generate Embedding|Not Available Via API yet|Y|N|Client Side Abstraction|||||N||

Footnotes:
- P = Partial Support
- <sup>1</sup> Only if you have the schema, to select the appropriate fields.
- <sup>2</sup> Supports broad categories of fields only.
- <sup>3</sup> Id is required in request, so can be returned if needed.
- <sup>4</sup> No strong typed support when specifying field list.

### Vector Store Cross Store support - Fields, types and indexing

|Feature|Azure AI Search|Weaviate|Redis|Chroma|FAISS|Pinecone|LLamaIndex|PostgreSql|Qdrant|Milvus|
|-|-|-|-|-|-|-|-|-|-|-|
|Field Differentiation|Fields|Key, Props, Vectors|Key, Fields|Key, Document, Metadata, Vector||Key, Metadata, SparseValues, Vector||Fields|Key, Props(Payload), Vectors|Fields|
|Multiple Vector per record support|Y|Y|Y|N||[N](https://docs.pinecone.io/guides/data/upsert-data#upsert-records-with-metadata)||Y|Y|Y|
|Index to Collection|1 to 1|1 to 1|1 to many|1 to 1|-|1 to 1|-|1 to 1|1 to 1|1 to 1|
|Id Type|String|UUID|string with collection name prefix|string||string|UUID|64Bit Int / UUID / ULID|64Bit Unsigned Int / UUID|Int64 / varchar|
|Supported Vector Types|[Collection(Edm.Byte) / Collection(Edm.Single) / Collection(Edm.Half) / Collection(Edm.Int16) / Collection(Edm.SByte)](https://learn.microsoft.com/en-us/rest/api/searchservice/supported-data-types)|float32|FLOAT32 and FLOAT64|||[Rust f32](https://docs.pinecone.io/troubleshooting/embedding-values-changed-when-upserted)||[single-precision (4 byte float) / half-precision (2 byte float) / binary (1bit) / sparse vectors (4 bytes)](https://github.com/pgvector/pgvector?tab=readme-ov-file#pgvector)|UInt8 / Float32|Binary / Float32 / Float16 / BFloat16 / SparseFloat|
|Supported Distance Functions|[Cosine / dot prod / euclidean dist (l2 norm)](https://learn.microsoft.com/en-us/azure/search/vector-search-ranking#similarity-metrics-used-to-measure-nearness)|[Cosine dist / dot prod / Squared L2 dist / hamming (num of diffs) / manhattan dist](https://weaviate.io/developers/weaviate/config-refs/distances#available-distance-metrics)|[Euclidean dist (L2) / Inner prod (IP) / Cosine dist](https://redis.io/docs/latest/develop/interact/search-and-query/advanced-concepts/vectors/)|[Squared L2 / Inner prod / Cosine similarity](https://docs.trychroma.com/guides#changing-the-distance-function)||[cosine sim / euclidean dist / dot prod](https://docs.pinecone.io/reference/api/control-plane/create_index)||[L2 dist / inner prod / cosine dist / L1 dist / Hamming dist / Jaccard dist (NB: Specified at query time, not index creation time)](https://github.com/pgvector/pgvector?tab=readme-ov-file#pgvector)|[Dot prod / Cosine sim / Euclidean dist (L2) / Manhattan dist](https://qdrant.tech/documentation/concepts/search/)|[Cosine sim / Euclidean dist / Inner Prod](https://milvus.io/docs/index-vector-fields.md)|
|Supported index types|[Exhaustive KNN (FLAT) / HNSW](https://learn.microsoft.com/en-us/azure/search/vector-search-ranking#algorithms-used-in-vector-search)|[HNSW / Flat / Dynamic](https://weaviate.io/developers/weaviate/config-refs/schema/vector-index)|[HNSW / FLAT](https://redis.io/docs/latest/develop/interact/search-and-query/advanced-concepts/vectors/#create-a-vector-field)|[HNSW not configurable](https://cookbook.chromadb.dev/core/concepts/#vector-index-hnsw-index)||[PGA](https://www.pinecone.io/blog/hnsw-not-enough/)||[HNSW / IVFFlat](https://github.com/pgvector/pgvector?tab=readme-ov-file#indexing)|[HNSW for dense](https://qdrant.tech/documentation/concepts/indexing/#vector-index)|<p>[In Memory: FLAT / IVF_FLAT / IVF_SQ8 / IVF_PQ / HNSW / SCANN](https://milvus.io/docs/index.md)</p><p>[On Disk: DiskANN](https://milvus.io/docs/disk_index.md)</p><p>[GPU: GPU_CAGRA / GPU_IVF_FLAT / GPU_IVF_PQ / GPU_BRUTE_FORCE](https://milvus.io/docs/gpu_index.md)</p>|

Footnotes:
- HNSW = Hierarchical Navigable Small World (HNSW performs an [approximate nearest neighbor (ANN)](https://learn.microsoft.com/en-us/azure/search/vector-search-overview#approximate-nearest-neighbors) search)
- KNN = k-nearest neighbors (performs a brute-force search that scans the entire vector space)
- IVFFlat = Inverted File with Flat Compression (This index type uses approximate nearest neighbor search (ANNS) to provide fast searches)
- Weaviate Dynamic = Starts as flat and switches to HNSW if the number of objects exceed a limit
- PGA = [Pinecone Graph Algorithm](https://www.pinecone.io/blog/hnsw-not-enough/)

### Vector Store Cross Store support - Search and filtering

|Feature|Azure AI Search|Weaviate|Redis|Chroma|FAISS|Pinecone|LLamaIndex|PostgreSql|Qdrant|Milvus|
|-|-|-|-|-|-|-|-|-|-|-|
|Index allows text search|Y|Y|Y|Y (On Metadata by default)||[Only in combination with Vector](https://docs.pinecone.io/guides/data/understanding-hybrid-search)||Y (with TSVECTOR field)|Y|Y|
|Text search query format|[Simple or Full Lucene](https://learn.microsoft.com/en-us/azure/search/search-query-create?tabs=portal-text-query#choose-a-query-type-simple--full)|[wildcard](https://weaviate.io/developers/weaviate/search/filters#filter-text-on-partial-matches)|wildcard & fuzzy|[contains & not contains](https://docs.trychroma.com/guides#filtering-by-document-contents)||Text only||[wildcard & binary operators](https://www.postgresql.org/docs/16/textsearch-controls.html#TEXTSEARCH-PARSING-QUERIES)|[Text only](https://qdrant.tech/documentation/concepts/filtering/#full-text-match)|[wildcard](https://milvus.io/docs/single-vector-search.md#Filtered-search)|
|Multi Field Vector Search Support|Y|[N](https://weaviate.io/developers/weaviate/search/similarity)||N (no multi vector support)||N||[Unclear due to order by syntax](https://github.com/pgvector/pgvector?tab=readme-ov-file#querying)|[N](https://qdrant.tech/documentation/concepts/search/)|[Y](https://milvus.io/api-reference/restful/v2.4.x/v2/Vector%20(v2)/Hybrid%20Search.md)|
|Targeted Multi Field Text Search Support|Y|[Y](https://weaviate.io/developers/weaviate/search/hybrid#set-weights-on-property-values)|[Y](https://redis.io/docs/latest/develop/interact/search-and-query/advanced-concepts/query_syntax/#field-modifiers)|N (only on document)||N||Y|Y|Y|
|Vector per Vector Field for Search|Y|N/A||N/A|||N/A||N/A|N/A|[Y](https://milvus.io/docs/multi-vector-search.md#Step-1-Create-Multiple-AnnSearchRequest-Instances)|
|Separate text search query from vectors|Y|[Y](https://weaviate.io/developers/weaviate/search/hybrid#specify-a-search-vector)|Y|Y||Y||Y|Y|[Y](https://milvus.io/api-reference/restful/v2.4.x/v2/Vector%20(v2)/Hybrid%20Search.md)|
|Allows filtering|Y|Y|Y (on TAG)|Y (On Metadata by default)||[Y](https://docs.pinecone.io/guides/indexes/configure-pod-based-indexes#selective-metadata-indexing)||Y|Y|Y|
|Allows filter grouping|Y (Odata)|[Y](https://weaviate.io/developers/weaviate/search/filters#nested-filters)||[Y](https://docs.trychroma.com/guides#using-logical-operators)||Y||Y|[Y](https://qdrant.tech/documentation/concepts/filtering/#clauses-combination)|[Y](https://milvus.io/docs/get-and-scalar-query.md#Use-Basic-Operators)|
|Allows scalar index field setup|Y|Y|Y|N||Y||Y|Y|Y|
|Requires scalar index field setup to filter|Y|Y|Y|N||N (on by default for all)||N|N|N (can filter without index)|

### Support for different mappers

Mapping between data models and the storage models can also require custom logic depending on the type of data model and storage model involved.

I'm therefore proposing that we allow mappers to be injectable for each `VectorStoreCollection` instance. The interfaces for these would vary depending
on the storage models used by each vector store and any unique capabilities that each vector store may have, e.g. qdrant can operate in `single` or
`multiple named vector` modes, which means the mapper needs to know whether to set a single vector or fill a vector map.

In addition to this, we should build first party mappers for each of the vector stores, which will cater for built in, generic models or use metadata to perform the mapping.

### Support for different storage schemas

The different stores vary in many ways around how data is organized.
- Some just store a record with fields on it, where fields can be a key or a data field or a vector and their type is determined at collection creation time.
- Others separate fields by type when interacting with the api, e.g. you have to specify a key explicitly, put metadata into a metadata dictionary and put vectors into a vector array.

I'm proposing that we allow two ways in which to provide the information required to map data between the consumer data model and storage data model.
First is a set of configuration objects that capture the types of each field. Second would be a set of attributes that can be used to decorate the model itself
and can be converted to the configuration objects, allowing a single execution path.
Additional configuration properties can easily be added for each type of field as required, e.g. IsFilterable or IsFullTextSearchable, allowing us to also create an index from the provided configuration.

I'm also proposing that even though similar attributes already exist in other systems, e.g. System.ComponentModel.DataAnnotations.KeyAttribute, we create our own.
We will likely require additional properties on all these attributes that are not currently supported on the existing attributes, e.g. whether a field is or
should be filterable. Requiring users to switch to new attributes later will be disruptive.

Here is what the attributes would look like, plus a sample use case.

```cs
sealed class VectorStoreRecordKeyAttribute : Attribute
{
}
sealed class VectorStoreRecordDataAttribute : Attribute
{
    public bool HasEmbedding { get; set; }
    public string EmbeddingPropertyName { get; set; }
}
sealed class VectorStoreRecordVectorAttribute : Attribute
{
}

public record HotelInfo(
    [property: VectorStoreRecordKey, JsonPropertyName("hotel-id")] string HotelId,
    [property: VectorStoreRecordData, JsonPropertyName("hotel-name")] string HotelName,
    [property: VectorStoreRecordData(HasEmbedding = true, EmbeddingPropertyName = "DescriptionEmbeddings"), JsonPropertyName("description")] string Description,
    [property: VectorStoreRecordVector, JsonPropertyName("description-embeddings")] ReadOnlyMemory<float>? DescriptionEmbeddings);
```

Here is what the configuration objects would look like.

```cs
abstract class VectorStoreRecordProperty(string propertyName);

sealed class VectorStoreRecordKeyProperty(string propertyName): Field(propertyName)
{
}
sealed class VectorStoreRecordDataProperty(string propertyName): Field(propertyName)
{
    bool HasEmbedding;
    string EmbeddingPropertyName;
}
sealed class VectorStoreRecordVectorProperty(string propertyName): Field(propertyName)
{
}

sealed class VectorStoreRecordDefinition
{
    IReadOnlyList<VectorStoreRecordProperty> Properties;
}
```

### Notable method signature changes from existing interface

All methods currently existing on IMemoryStore will be ported to new interfaces, but in places I am proposing that we make changes to improve
consistency and scalability.

1. `RemoveAsync` and `RemoveBatchAsync` renamed to `DeleteAsync` and `DeleteBatchAsync`, since record are actually deleted, and this also matches the verb used for collections.
2. `GetCollectionsAsync` renamed to `GetCollectionNamesAsync`, since we are only retrieving names and no other information about collections.
3. `DoesCollectionExistAsync` renamed to `CollectionExistsAsync` since this is shorter and is more commonly used in other apis.

### Comparison with other AI frameworks

|Criteria|Current SK Implementation|Proposed SK Implementation|Spring AI|LlamaIndex|Langchain|
|-|-|-|-|-|-|
|Support for Custom Schemas|N|Y|N|N|N|
|Naming of store|MemoryStore|VectorStore, VectorStoreCollection|VectorStore|VectorStore|VectorStore|
|MultiVector support|N|Y|N|N|N|
|Support Multiple Collections via SDK params|Y|Y|N (via app config)|Y|Y|

## Decision Drivers

From GitHub Issue:
- API surface must be easy to use and intuitive
- Alignment with other patterns in the SK
- - Design must allow Memory Plugins to be easily instantiated with any connector
- Design must support all Kernel content types
- Design must allow for database specific configuration
- All NFR's to be production ready are implemented (see Roadmap for more detail)
- Basic CRUD operations must be supported so that connectors can be used in a polymorphic manner
- Official Database Clients must be used where available
- Dynamic database schema must be supported
- Dependency injection must be supported
- Azure-ML YAML format must be supported
- Breaking glass scenarios must be supported

## Considered Questions

1. Combined collection and record management vs separated.
2. Collection name and key value normalization in decorator or main class.
3. Collection name as method param or constructor param.
4. How to normalize ids across different vector stores where different types are supported.
5. Store Interface/Class Naming

### Question 1: Combined collection and record management vs separated.

#### Option 1 - Combined collection and record management

```cs
interface IVectorRecordStore<TRecord>
{
    Task CreateCollectionAsync(CollectionCreateConfig collectionConfig, CancellationToken cancellationToken = default);
    IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default);
    Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default);
    Task DeleteCollectionAsync(string name, CancellationToken cancellationToken = default);

    Task UpsertAsync(TRecord data, CancellationToken cancellationToken = default);
    IAsyncEnumerable<string> UpsertBatchAsync(IEnumerable<TRecord> dataSet, CancellationToken cancellationToken = default);
    Task<TRecord> GetAsync(string key, bool withEmbedding = false, CancellationToken cancellationToken = default);
    IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<string> keys, bool withVectors = false, CancellationToken cancellationToken = default);
    Task DeleteAsync(string key, CancellationToken cancellationToken = default);
    Task DeleteBatchAsync(IEnumerable<string> keys, CancellationToken cancellationToken = default);
}

class AzureAISearchVectorRecordStore<TRecord>(
    Azure.Search.Documents.Indexes.SearchIndexClient client,
    Schema schema): IVectorRecordStore<TRecord>;

class WeaviateVectorRecordStore<TRecord>(
    WeaviateClient client,
    Schema schema): IVectorRecordStore<TRecord>;

class RedisVectorRecordStore<TRecord>(
    StackExchange.Redis.IDatabase database,
    Schema schema): IVectorRecordStore<TRecord>;
```

#### Option 2 - Separated collection and record management with opinionated create implementations

```cs

interface IVectorCollectionStore
{
    virtual Task CreateChatHistoryCollectionAsync(string name, CancellationToken cancellationToken = default);
    virtual Task CreateSemanticCacheCollectionAsync(string name, CancellationToken cancellationToken = default);

    IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default);
    Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default);
    Task DeleteCollectionAsync(string name, CancellationToken cancellationToken = default);
}

class AzureAISearchVectorCollectionStore: IVectorCollectionStore;
class RedisVectorCollectionStore: IVectorCollectionStore;
class WeaviateVectorCollectionStore: IVectorCollectionStore;

// Customers can inherit from our implementations and replace just the creation scenarios to match their schemas.
class CustomerCollectionStore: AzureAISearchVectorCollectionStore, IVectorCollectionStore;

// We can also create implementations that create indices based on an MLIndex specification.
class MLIndexAzureAISearchVectorCollectionStore(MLIndex mlIndexSpec): AzureAISearchVectorCollectionStore, IVectorCollectionStore;

interface IVectorRecordStore<TRecord>
{
    Task<TRecord?> GetAsync(string key, GetRecordOptions? options = default, CancellationToken cancellationToken = default);
    Task DeleteAsync(string key, DeleteRecordOptions? options = default, CancellationToken cancellationToken = default);
    Task<string> UpsertAsync(TRecord record, UpsertRecordOptions? options = default, CancellationToken cancellationToken = default);
}

class AzureAISearchVectorRecordStore<TRecord>(): IVectorRecordStore<TRecord>;
```

#### Option 3 - Separated collection and record management with collection create separate from other operations.

Vector store same as option 2 so not repeated for brevity.

```cs

interface IVectorCollectionCreate
{
    virtual Task CreateCollectionAsync(string name, CancellationToken cancellationToken = default);
}

// Implement a generic version of create that takes a configuration that should work for 80% of cases.
class AzureAISearchConfiguredVectorCollectionCreate(CollectionCreateConfig collectionConfig): IVectorCollectionCreate;

// Allow custom implementations of create for break glass scenarios for outside the 80% case.
class AzureAISearchChatHistoryVectorCollectionCreate: IVectorCollectionCreate;
class AzureAISearchSemanticCacheVectorCollectionCreate: IVectorCollectionCreate;

// Customers can create their own creation scenarios to match their schemas, but can continue to use our get, does exist and delete class.
class CustomerChatHistoryVectorCollectionCreate: IVectorCollectionCreate;

interface IVectorCollectionNonSchema
{
    IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default);
    Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default);
    Task DeleteCollectionAsync(string name, CancellationToken cancellationToken = default);
}

class AzureAISearchVectorCollectionNonSchema: IVectorCollectionNonSchema;
class RedisVectorCollectionNonSchema: IVectorCollectionNonSchema;
class WeaviateVectorCollectionNonSchema: IVectorCollectionNonSchema;

```

#### Option 4 - Separated collection and record management with collection create separate from other operations, with collection management aggregation class on top.

Variation on option 3. 

```cs

interface IVectorCollectionCreate
{
    virtual Task CreateCollectionAsync(string name, CancellationToken cancellationToken = default);
}

interface IVectorCollectionNonSchema
{
    IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default);
    Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default);
    Task DeleteCollectionAsync(string name, CancellationToken cancellationToken = default);
}

// DB Specific NonSchema implementations
class AzureAISearchVectorCollectionNonSchema: IVectorCollectionNonSchema;
class RedisVectorCollectionNonSchema: IVectorCollectionNonSchema;

// Combined Create + NonSchema Interface
interface IVectorCollectionStore: IVectorCollectionCreate, IVectorCollectionNonSchema {}

// Base abstract class that forwards non-create operations to provided implementation.
abstract class VectorCollectionStore(IVectorCollectionNonSchema collectionNonSchema): IVectorCollectionStore
{
    public abstract Task CreateCollectionAsync(string name, CancellationToken cancellationToken = default);
    public IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default) { return collectionNonSchema.ListCollectionNamesAsync(cancellationToken); }
    public Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default) { return collectionNonSchema.CollectionExistsAsync(name, cancellationToken); }
    public Task DeleteCollectionAsync(string name, CancellationToken cancellationToken = default) { return collectionNonSchema.DeleteCollectionAsync(name, cancellationToken); }
}

// Collections store implementations, that inherit from base class, and just adds the different creation implementations.
class AzureAISearchChatHistoryVectorCollectionStore(AzureAISearchVectorCollectionNonSchema nonSchema): VectorCollectionStore(nonSchema);
class AzureAISearchSemanticCacheVectorCollectionStore(AzureAISearchVectorCollectionNonSchema nonSchema): VectorCollectionStore(nonSchema);
class AzureAISearchMLIndexVectorCollectionStore(AzureAISearchVectorCollectionNonSchema nonSchema): VectorCollectionStore(nonSchema);

// Customer collections store implementation, that uses the base Azure AI Search implementation for get, doesExist and delete, but adds its own creation.
class ContosoProductsVectorCollectionStore(AzureAISearchVectorCollectionNonSchema nonSchema): VectorCollectionStore(nonSchema);

```

#### Option 5 - Separated collection and record management with collection create separate from other operations, with overall aggregation class on top.

Same as option 3 / 4, plus:

```cs

interface IVectorStore : IVectorCollectionStore, IVectorRecordStore
{    
}

// Create a static factory that produces one of these, so only the interface is public, not the class.
internal class VectorStore<TRecord>(IVectorCollectionCreate create, IVectorCollectionNonSchema nonSchema, IVectorRecordStore<TRecord> records): IVectorStore
{
}

```

#### Option 6 - Collection store acts as factory for record store.

`IVectorStore` acts as a factory for `IVectorStoreCollection`, and any schema agnostic multi-collection operations are kept on `IVectorStore`.


```cs
public interface IVectorStore
{
    IVectorStoreCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null);
    IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default));
}

public interface IVectorStoreCollection<TKey, TRecord>
{
    public string Name { get; }

    // Collection Operations
    Task CreateCollectionAsync();
    Task<bool> CreateCollectionIfNotExistsAsync();
    Task<bool> CollectionExistsAsync();
    Task DeleteCollectionAsync();

    // Data manipulation
    Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = default, CancellationToken cancellationToken = default);
    IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<TKey> keys, GetRecordOptions? options = default, CancellationToken cancellationToken = default);
    Task DeleteAsync(TKey key, DeleteRecordOptions? options = default, CancellationToken cancellationToken = default);
    Task DeleteBatchAsync(IEnumerable<TKey> keys, DeleteRecordOptions? options = default, CancellationToken cancellationToken = default);
    Task<TKey> UpsertAsync(TRecord record, UpsertRecordOptions? options = default, CancellationToken cancellationToken = default);
    IAsyncEnumerable<TKey> UpsertBatchAsync(IEnumerable<TRecord> records, UpsertRecordOptions? options = default, CancellationToken cancellationToken = default);
}
```


#### Decision Outcome

Option 1 is problematic on its own, since we have to allow consumers to create custom implementations of collection create for break glass scenarios. With
a single interface like this, it will require them to implement many methods that they do not want to change. Options 4 & 5, gives us more flexibility while
still preserving the ease of use of an aggregated interface as described in Option 1.

Option 2 doesn't give us the flexbility we need for break glass scenarios, since it only allows certain types of collections to be created. It also means
that each time a new collection type is required it introduces a breaking change, so it is not a viable option.

Since collection create and configuration and the possible options vary considerable across different database types, we will need to support an easy
to use break glass scenario for collection creation. While we would be able to develop a basic configurable create option, for complex create scenarios
users will need to implement their own. We will also need to support multiple create implementations out of the box, e.g. a configuration based option using
our own configuration, create implementations that re-create the current model for backward compatibility, create implementations that use other configuration
as input, e.g. Azure-ML YAML. Therefore separating create, which may have many implementations, from exists, list and delete, which requires only a single implementation per database type is useful.
Option 3 provides us this separation, but Option 4 + 5 builds on top of this, and allows us to combine different implementations together for simpler
consumption.

Chosen option: 6

- Easy to use, and similar to many SDk implementations.
- Can pass a single object around for both collection and record access.

###  Question 2: Collection name and key value normalization in store, decorator or via injection.

#### Option 1 - Normalization in main record store

- Pros: Simple
- Cons: The normalization needs to vary separately from the record store, so this will not work

```cs
    public class AzureAISearchVectorStoreCollection<TRecord> : IVectorStoreCollection<TRecord>
    {
        ...

        // On input.
        var normalizedCollectionName = this.NormalizeCollectionName(collectionName);
        var encodedId = AzureAISearchMemoryRecord.EncodeId(key);

        ...

        // On output.
        DecodeId(this.Id)

        ...
    }
```

#### Option 2 - Normalization in decorator

- Pros: Allows normalization to vary separately from the record store.
- Pros: No code executed when no normalization required.
- Pros: Easy to package matching encoders/decoders together.
- Pros: Easier to obsolete encoding/normalization as a concept.
- Cons: Not a major con, but need to implement the full VectorStoreCollection interface, instead of e.g. just providing the two translation functions, if we go with option 3.
- Cons: Hard to have a generic implementation that can work with any model, without either changing the data in the provided object on upsert or doing cloning in an expensive way.

```cs
    new KeyNormalizingAISearchVectorStoreCollection<MyModel>(
        "keyField",
         new AzureAISearchVectorStoreCollection<MyModel>(...));
```

#### Option 3 - Normalization via optional function parameters to record store constructor

- Pros: Allows normalization to vary separately from the record store.
- Pros: No need to implement the full VectorStoreCollection interface.
- Pros: Can modify values on serialization without changing the incoming record, if supported by DB SDK.
- Cons: Harder to package matching encoders/decoders together.

```cs
public class AzureAISearchVectorStoreCollection<TRecord>(StoreOptions options);

public class StoreOptions
{
    public Func<string, string>? EncodeKey { get; init; }
    public Func<string, string>? DecodeKey { get; init; }
    public Func<string, string>? SanitizeCollectionName { get; init; }
}
```

#### Option 4 - Normalization via custom mapper

If developer wants to change any values they can do so by creating a custom mapper.

- Cons: Developer needs to implement a mapper if they want to do normalization.
- Cons: Developer cannot change collection name as part of the mapping.
- Pros: No new extension points required to support normalization.
- Pros: Developer can change any field in the record.

#### Decision Outcome

Chosen option 3, since it is similar to how we are doing mapper injection and would also work well in python.

Option 1 won't work because if e.g. the data was written using another tool, it may be unlikely that it was encoded using the same mechanism as supported here
and therefore this functionality may not be appropriate. The developer should have the ability to not use this functionality or
provide their own encoding / decoding behavior.

###  Question 3: Collection name as method param or via constructor or either

#### Option 1 - Collection name as method param

```cs
public class MyVectorStoreCollection()
{
    public async Task<TRecord?> GetAsync(string collectionName, string key, GetRecordOptions? options = default, CancellationToken cancellationToken = default);
}
```

#### Option 2 - Collection name via constructor

```cs
public class MyVectorStoreCollection(string defaultCollectionName)
{
    public async Task<TRecord?> GetAsync(string key, GetRecordOptions? options = default, CancellationToken cancellationToken = default);
}
```

#### Option 3 - Collection name via either

```cs
public class MyVectorStoreCollection(string defaultCollectionName)
{
    public async Task<TRecord?> GetAsync(string key, GetRecordOptions? options = default, CancellationToken cancellationToken = default);
}

public class GetRecordOptions
{
    public string CollectionName { get; init; };
}
```

#### Decision Outcome

Chosen option 2. None of the other options work with the decision outcome of Question 1, since that design requires the `VectorStoreCollection` to be tied to a single collection instance.

### Question 4: How to normalize ids across different vector stores where different types are supported.

#### Option 1 - Take a string and convert to a type that was specified on the constructor

```cs
public async Task<TRecord?> GetAsync(string key, GetRecordOptions? options = default, CancellationToken cancellationToken = default)
{
    var convertedKey = this.keyType switch
    {
        KeyType.Int => int.parse(key),
        KeyType.GUID => Guid.parse(key)
    }

    ...
}
```

- No additional overloads are required over time so no breaking changes.
- Most data types can easily be represented in string form and converted to/from it.

#### Option 2 - Take an object and cast to a type that was specified on the constructor.

```cs
public async Task<TRecord?> GetAsync(object key, GetRecordOptions? options = default, CancellationToken cancellationToken = default)
{
    var convertedKey = this.keyType switch
    {
        KeyType.Int => key as int,
        KeyType.GUID => key as Guid
    }

    if (convertedKey is null)
    {
        throw new InvalidOperationException($"The provided key must be of type {this.keyType}")
    }

    ...
}

```

- No additional overloads are required over time so no breaking changes.
- Any data types can be represented as object.

#### Option 3 - Multiple overloads where we convert where possible, throw when not possible.

```cs
public async Task<TRecord?> GetAsync(string key, GetRecordOptions? options = default, CancellationToken cancellationToken = default)
{
    var convertedKey = this.keyType switch
    {
        KeyType.Int => int.Parse(key),
        KeyType.String => key,
        KeyType.GUID => Guid.Parse(key)
    }
}
public async Task<TRecord?> GetAsync(int key, GetRecordOptions? options = default, CancellationToken cancellationToken = default)
{
    var convertedKey = this.keyType switch
    {
        KeyType.Int => key,
        KeyType.String => key.ToString(),
        KeyType.GUID => throw new InvalidOperationException($"The provided key must be convertible to a GUID.")
    }
}
public async Task<TRecord?> GetAsync(GUID key, GetRecordOptions? options = default, CancellationToken cancellationToken = default)
{
    var convertedKey = this.keyType switch
    {
        KeyType.Int => throw new InvalidOperationException($"The provided key must be convertible to an int.")
        KeyType.String => key.ToString(),
        KeyType.GUID => key
    }
}
```

- Additional overloads are required over time if new key types are found on new connectors, causing breaking changes.
- You can still call a method that causes a runtime error, when the type isn't supported.

#### Option 4 - Add key type as generic to interface

```cs
interface IVectorRecordStore<TRecord, TKey>
{
    Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = default, CancellationToken cancellationToken = default);
}

class AzureAISearchVectorRecordStore<TRecord, TKey>: IVectorRecordStore<TRecord, TKey>
{
    public AzureAISearchVectorRecordStore()
    {
        // Check if TKey matches the type of the field marked as a key on TRecord and throw if they don't match.
        // Also check if keytype is one of the allowed types for Azure AI Search and throw if it isn't.
    }
}

```

- No runtime issues after construction.
- More cumbersome interface.

#### Decision Outcome

Chosen option 4, since it is forwards compatible with any complex key types we may need to support but still allows
each implementation to hardcode allowed key types if the vector db only supports certain key types.

### Question 5: Store Interface/Class Naming.

#### Option 1 - VectorDB

```cs
interface IVectorDBRecordService {}
interface IVectorDBCollectionUpdateService {}
interface IVectorDBCollectionCreateService {}
```

#### Option 2 - Memory

```cs
interface IMemoryRecordService {}
interface IMemoryCollectionUpdateService {}
interface IMemoryCollectionCreateService {}
```

### Option 3 - VectorStore

```cs
interface IVectorRecordStore<TRecord> {}
interface IVectorCollectionNonSchema {}
interface IVectorCollectionCreate {}
interface IVectorCollectionStore {}: IVectorCollectionCreate, IVectorCollectionNonSchema
interface IVectorStore<TRecord> {}: IVectorCollectionStore, IVectorRecordStore<TRecord>
```

### Option 4 - VectorStore + VectorStoreCollection

```cs
interface IVectorStore
{
    IVectorStoreCollection GetCollection()
}
interface IVectorStoreCollection
{
    Get()
    Delete()
    Upsert()
}
```

#### Decision Outcome

Chosen option 4. The word memory is broad enough to encompass any data, so using it seems arbitrary. All competitors are using the term vector store, so using something similar is good for recognition.
Option 4 also matches our design as chosen in question 1.

## Usage Examples

### DI Framework: .net 8 Keyed Services

```cs
class CacheEntryModel(string prompt, string result, ReadOnlyMemory<float> promptEmbedding);

class SemanticTextMemory(IVectorStore configuredVectorStore, VectorStoreRecordDefinition? vectorStoreRecordDefinition): ISemanticTextMemory
{
    public async Task SaveInformation<TDataType>(string collectionName, TDataType record)
    {
        var collection = vectorStore.GetCollection<TDataType>(collectionName, vectorStoreRecordDefinition);
        if (!await collection.CollectionExists())
        {
            await collection.CreateCollection();
        }
        await collection.UpsertAsync(record);
    }
}

class CacheSetFunctionFilter(ISemanticTextMemory memory); // Saves results to cache.
class CacheGetPromptFilter(ISemanticTextMemory memory);   // Check cache for entries.

var builder = Kernel.CreateBuilder();

builder
    // Existing registration:
    .AddAzureOpenAITextEmbeddingGeneration(textEmbeddingDeploymentName, azureAIEndpoint, apiKey, serviceId: "AzureOpenAI:text-embedding-ada-002")

    // Register an IVectorStore implementation under the given key.
    .AddAzureAISearch("Cache", azureAISearchEndpoint, apiKey, new Options() { withEmbeddingGeneration = true });

// Add Semantic Cache Memory for the cache entry model.
builder.Services.AddTransient<ISemanticTextMemory>(sp => {
    return new SemanticTextMemory(
        sp.GetKeyedService<IVectorStore>("Cache"),
        cacheRecordDefinition);
});

// Add filter to retrieve items from cache and one to add items to cache.
// Since these filters depend on ISemanticTextMemory<CacheEntryModel> and that is already registered, it should get matched automatically.
builder.Services.AddTransient<IPromptRenderFilter, CacheGetPromptFilter>();
builder.Services.AddTransient<IFunctionInvocationFilter, CacheSetFunctionFilter>();
```

## Roadmap

### Record Management

1. Release VectorStoreCollection public interface and implementations for Azure AI Search, Qdrant and Redis.
2. Add support for registering record stores with SK container to allow automatic dependency injection.
3. Add VectorStoreCollection implementations for remaining stores.

### Collection Management

4. Release Collection Management public interface and implementations for Azure AI Search, Qdrant and Redis.
5. Add support for registering collection management with SK container to allow automatic dependency injection.
6. Add Collection Management implementations for remaining stores.

### Collection Creation

7. Release Collection Creation public interface.
8. Create cross db collection creation config that supports common functionality, and per daatabase implementation that supports this configuration.
9. Add support for registering collection creation with SK container to allow automatic dependency injection.

### First Party Memory Features and well known model support

10. Add model and mappers for legacy SK MemoryStore interface, so that consumers using this has an upgrade path to the new memory storage stack.
11. Add model and mappers for popular loader systems, like Kernel Memory or LlamaIndex.
11. Explore adding first party implementations for common scenarios, e.g. semantic caching. Specfics TBD.

### Cross Cutting Requirements

Need the following for all features:

- Unit tests
- Integration tests
- Logging / Telemetry
- Common Exception Handling
- Samples, including:
  - Usage scenario for collection and record management using custom model and configured collection creation.
  - A simple consumption example like semantic caching, specfics TBD.
  - Adding your own collection creation implementation.
  - Adding your own custom model mapper.
- Documentation, including:
  - How to create models and annotate/describe them to use with the storage system.
  - How to define configuration for creating collections using common create implementation.
  - How to use record and collection management apis.
  - How to implement your own collection create implementation for break glass scenario.
  - How to implement your own mapper.
  - How to upgrade from the current storage system to the new one.
