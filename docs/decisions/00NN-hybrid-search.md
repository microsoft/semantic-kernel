---
# These are optional elements. Feel free to remove any of them.
status: {proposed | rejected | accepted | deprecated | � | superseded by [ADR-0001](0001-madr-architecture-decisions.md)}
contact: westey-m
date: 2024-11-27
deciders: {list everyone involved in the decision}
consulted: {list everyone whose opinions are sought (typically subject-matter experts); and with whom there is a two-way communication}
informed: {list everyone who is kept up-to-date on progress; and with whom there is a one-way communication}
---

# Support Hybrid Search in VectorStore abstractions

## Context and Problem Statement

In addition to simple vector search, many databases also support Hybrid search.
Hybrid search typically results in higher quality search results, and therefore the ability to do Hybrid search via VectorStore abstractions
is an important feature to add.

The way in which Hybrid search is supported varies by database. The two most common ways of supporting hybrid search is:

1. Using dense vector search and keyword/fulltext search in parallel, and then combining the results.
1. Using dense vector search and sparse vector search in parallel, and then combining the results.

Sparse vectors are different from dense vectors in that they typically have many more dimensions, but with many of the dimensions being zero.
Sparse vectors, when used with text search, have a dimension for each word/token in a vocabulary, with the value indicating the importance of the word
in the source text.
The more common the word in a specific chunk of text, and the less common the word is in the corpus, the higher the value in the sparse vector.

There are various mechanisms for generating sparse vectors, such as

- [TF-IDF](https://en.wikipedia.org/wiki/Tf%E2%80%93idf)
- [SPLADE](https://www.pinecone.io/learn/splade/)
- [BGE-m3 sparse embedding model](https://huggingface.co/BAAI/bge-m3).
- [pinecone-sparse-english-v0](https://docs.pinecone.io/models/pinecone-sparse-english-v0)

While these are supported well in Python, they are not well supported in .net today.
Adding support for generating sparse vectors is out of scope of this ADR.

More background information:

- [Background article from Qdrant about using sparse vectors for Hybrid Search](https://qdrant.tech/articles/sparse-vectors)
- [TF-IDF explainer for beginners](https://medium.com/@coldstart_coder/understanding-and-implementing-tf-idf-in-python-a325d1301484)

ML.Net contains an implementation of TF-IDF that could be used to generate sparse vectors in .net. See [here](https://github.com/dotnet/machinelearning/blob/886e2ff125c0060f5a251056c7eb2a7d28738984/docs/samples/Microsoft.ML.Samples/Dynamic/Transforms/Text/ProduceWordBags.cs#L55-L105) for an example.

### Hybrid search support in different databases

|Feature|Azure AI Search|Weaviate|Redis|Chroma|Pinecone|PostgreSql|Qdrant|Milvus|Elasticsearch|CosmosDB NoSql|MongoDB|
|-|-|-|-|-|-|-|-|-|-|-|-|
|Hybrid search supported|Y|Y|N (No parallel execution with fusion)|N|Y|Y|Y|Y|Y|Y|Y|
|Hybrid search definition|Vector + FullText|[Vector + Keyword (BM25F)](https://weaviate.io/developers/weaviate/search/hybrid)|||[Vector + Sparse Vector for keywords](https://docs.pinecone.io/guides/get-started/key-features#hybrid-search)|[Vector + Keyword](https://jkatz05.com/post/postgres/hybrid-search-postgres-pgvector/)|[Vector + SparseVector / Keyword](https://qdrant.tech/documentation/concepts/hybrid-queries/)|[Vector + SparseVector](https://milvus.io/docs/multi-vector-search.md)|Vector + FullText|[Vector + Fulltext (BM25)](https://learn.microsoft.com/en-us/azure/cosmos-db/gen-ai/hybrid-search)|[Vector + FullText](https://www.mongodb.com/docs/atlas/atlas-search/tutorial/hybrid-search)|
|Fusion method configurable|N|Y|||?|Y|Y|Y|Y, but only one option|Y, but only one option|N|
|Fusion methods|[RRF](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking)|Ranked/RelativeScore|||?|[Build your own](https://jkatz05.com/post/postgres/hybrid-search-postgres-pgvector/)|RRF / DBSF|[RRF / Weighted](https://milvus.io/docs/multi-vector-search.md)|[RRF](https://www.elastic.co/search-labs/tutorials/search-tutorial/vector-search/hybrid-search)|[RRF](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/query/rrf)|[RRF](https://www.mongodb.com/docs/atlas/atlas-search/tutorial/hybrid-search)|
|Hybrid Search Input Params|Vector + string|[Vector + string](https://weaviate.io/developers/weaviate/api/graphql/search-operators#hybrid)|||Vector + SparseVector|Vector + String|[Vector + SparseVector](https://qdrant.tech/documentation/concepts/hybrid-queries/)|[Vector + SparseVector](https://milvus.io/docs/multi-vector-search.md)|Vector + string|Vector + string array|Vector + string|
|Sparse Distance Function|n/a|n/a|||[dotproduct only for both dense and sparse, 1 setting for both](https://docs.pinecone.io/guides/data/understanding-hybrid-search#sparse-dense-workflow)|n/a|dotproduct|Inner Product|n/a|n/a|n/a|
|Sparse Indexing options|n/a|n/a|||no separate config to dense|n/a|ondisk / inmemory  + IDF|[SPARSE_INVERTED_INDEX / SPARSE_WAND](https://milvus.io/docs/index.md?tab=sparse)|n/a|n/a|n/a|
|Sparse data model|n/a|n/a|||[indices & values arrays](https://docs.pinecone.io/guides/data/upsert-sparse-dense-vectors)|n/a|indices & values arrays|[sparse matrix / List of dict / list of tuples](https://milvus.io/docs/sparse_vector.md#Use-sparse-vectors-in-Milvus)|n/a|n/a|n/a|
|Keyword matching behavior|[Space Separated with SearchMode=any does OR, searchmode=all does AND](https://learn.microsoft.com/en-us/azure/search/search-lucene-query-architecture)|[Tokenization with split by space, affects ranking](https://weaviate.io/developers/weaviate/search/bm25)|||n/a|[Tokenization](https://www.postgresql.org/docs/current/textsearch-controls.html)|[<p>No FTS Index: Exact Substring match</p><p>FTS Index present: All words must be present</p>](https://qdrant.tech/documentation/concepts/filtering/#full-text-match)|n/a|[And/Or capabilities](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-match-bool-prefix-query.html)|-|[Allows multiple multi-word phrases with OR](https://www.mongodb.com/docs/atlas/atlas-search/phrase/) and [a single multi-word prhase where the words can be OR'd or AND'd](https://www.mongodb.com/docs/atlas/atlas-search/text/)|

Glossary:

- RRF = Reciprical Rank Fusion
- DBSF = Distribution-Based Score Fusion
- IDF = Inverse Document Frequency

### Language required for Cosmos DB NoSQL full text search configuration

Cosmos DB NoSQL requires a language to be specified for full text search and it requires full text search indexing for hybrid search to be enabled.
We therefore need to support a way of specifying the language when creating the index.

Cosmos DB NoSQL is the only database from our sample that has a required setting of this type.

|Feature|Azure AI Search|Weaviate|Redis|Chroma|Pinecone|PostgreSql|Qdrant|Milvus|Elasticsearch|CosmosDB NoSql|MongoDB|
|-|-|-|-|-|-|-|-|-|-|-|-|
|Requires FullTextSearch indexing for hybrid search|Y|Y|n/a|n/a|n/a|Y|N [optional](https://qdrant.tech/documentation/concepts/filtering/#full-text-match)|n/a|Y|Y|[Y](https://www.mongodb.com/docs/atlas/atlas-search/tutorial/hybrid-search/?msockid=04b550d92f2f619c271a45a42e066050#create-the-atlas-vector-search-and-fts-indexes)|
|Required FullTextSearch index options|None required, [many optional](https://learn.microsoft.com/en-us/rest/api/searchservice/indexes/create?view=rest-searchservice-2024-07-01&tabs=HTTP)|None required, [none optional](https://weaviate.io/developers/weaviate/concepts/indexing#collections-without-indexes)||||[language required](https://jkatz05.com/post/postgres/hybrid-search-postgres-pgvector/)|none required, [some optional](https://qdrant.tech/documentation/concepts/indexing/#full-text-index)||None required, [many optional](https://elastic.github.io/elasticsearch-net/8.16.3/api/Elastic.Clients.Elasticsearch.Mapping.TextProperty.html)|Language Required|None required, [many optional](https://www.mongodb.com/docs/atlas/atlas-search/field-types/string-type/#configure-fts-field-type-field-properties)|

### Keyword Search interface options

Each DB has different keyword search capabilities. Some only support a very basic interface when it comes to listing keywords for hybrid search. The following table is to list the compatibility of each DB with a specific keyword public interface we may want to support.

|Feature|Azure AI Search|Weaviate|PostgreSql|Qdrant|Elasticsearch|CosmosDB NoSql|MongoDB|
|-|-|-|-|-|-|-|-|
|<p>string[] keyword</p><p>One word per element</p><p>Any matching word boosts ranking.</p>|Y|Y (have to join with spaces)|[Y (have to join with spaces)](https://www.postgresql.org/docs/current/textsearch-controls.html)|Y (via filter with multiple OR'd matches)|Y|Y|[Y (have to join with spaces)](https://www.mongodb.com/docs/drivers/node/current/fundamentals/crud/read-operations/text/)|
|<p>string[] keyword</p><p>One or more words per element</p><p>All words in a single element have to be present to boost the ranking.</p>|Y|N|Y|Y (via filter with multiple OR'd matches and FTS Index)|-|N|N|
|<p>string[] keyword</p><p>One or more words per element</p><p>Multiple words in a single element is a phrase that must match exactly to boost the ranking.</p>|Y|N|Y|Only via filter with multiple OR'd matches and NO Index|-|N|Y|
|<p>string keyword</p><p>Space separated words</p><p>Any matching word boosts ranking.</p>|Y|Y|Y|N (would need to split words)|-|N (would need to split words)|Y|

### Naming Options

|Interface Name|Method Name|Parameters|Options Class Name|Keyword Property Selector|Dense Vector Property Selector|
|-|-|-|-|-|-|
|KeywordVectorizedHybridSearch|KeywordVectorizedHybridSearch|string[] + Dense Vector|KeywordVectorizedHybridSearchOptions|FullTextPropertyName|VectorPropertyName|
|SparseVectorizedHybridSearch|SparseVectorizedHybridSearch|Sparse Vector + Dense Vector|SparseVectorizedHybridSearchOptions|SparseVectorPropertyName|VectorPropertyName|
|KeywordVectorizableTextHybridSearch|KeywordVectorizableTextHybridSearch|string[] + string|KeywordVectorizableTextHybridSearchOptions|FullTextPropertyName|VectorPropertyName|
|SparseVectorizableTextHybridSearch|SparseVectorizableTextHybridSearch|string[] + string|SparseVectorizableTextHybridSearchOptions|SparseVectorPropertyName|VectorPropertyName|

|Interface Name|Method Name|Parameters|Options Class Name|Keyword Property Selector|Dense Vector Property Selector|
|-|-|-|-|-|-|
|KeywordVectorizedHybridSearch|HybridSearch|string[] + Dense Vector|KeywordVectorizedHybridSearchOptions|FullTextPropertyName|VectorPropertyName|
|SparseVectorizedHybridSearch|HybridSearch|Sparse Vector + Dense Vector|SparseVectorizedHybridSearchOptions|SparseVectorPropertyName|VectorPropertyName|
|KeywordVectorizableTextHybridSearch|HybridSearch|string[] + string|KeywordVectorizableTextHybridSearchOptions|FullTextPropertyName|VectorPropertyName|
|SparseVectorizableTextHybridSearch|HybridSearch|string[] + string|SparseVectorizableTextHybridSearchOptions|SparseVectorPropertyName|VectorPropertyName|

|Interface Name|Method Name|Parameters|Options Class Name|Keyword Property Selector|Dense Vector Property Selector|
|-|-|-|-|-|-|
|HybridSearchWithKeywords|HybridSearch|string[] + Dense Vector|HybridSearchOptions|FullTextPropertyName|VectorPropertyName|
|HybridSearchWithSparseVector|HybridSearchWithSparseVector|Sparse Vector + Dense Vector|HybridSearchWithSparseVectorOptions|SparseVectorPropertyName|VectorPropertyName|
|HybridSearchWithKeywordsAndVectorizableText|HybridSearch|string[] + string|HybridSearchOptions|FullTextPropertyName|VectorPropertyName|
|HybridSearchWithVectorizableKeywordsAndText|HybridSearchWithSparseVector|string[] + string|HybridSearchWithSparseVectorOptions|SparseVectorPropertyName|VectorPropertyName|

|Area|Type of search|Method Name|
|-|-|-|
|**Non-vector Search**|||
|Non-vector Search||Search|
|**Vector Search**|||
|Vector Search|With Vector|VectorSearch|
|Vector Search|With Vectorizable Text (string)|VectorSearchWithText|
|Vector Search|With Vectorizable Image (string/byte[]/other)|VectorSearchWithImage|
|**Hybrid Search**|||
|Hybrid Search|With DenseVector and string[] keywords|HybridSearch|
|Hybrid Search|With vectorizable string and string[] keywords|HybridSearch|
|Hybrid Search|With DenseVector and SparseVector|HybridSearchWithSparseVector|
|Hybrid Search|With vectorizable string and sparse vectorisable string[] keywords|HybridSearchWithSparseVector|

### Keyword based hybrid search

```csharp
interface IKeywordVectorizedHybridSearch<TRecord>
{
    Task<VectorSearchResults<TRecord>> KeywordVectorizedHybridSearch<TVector>(
        TVector vector,
        ICollection<string> keywords,
        KeywordVectorizedHybridSearchOptions options,
        CancellationToken cancellationToken);
}

class KeywordVectorizedHybridSearchOptions
{
    // The name of the property to target the vector search against.
    public string? VectorPropertyName { get; init; }

    // The name of the property to target the text search against.
    public string? FullTextPropertyName { get; init; }

    public VectorSearchFilter? Filter { get; init; }
    public int Top { get; init; } = 3;
    public int Skip { get; init; } = 0;
    public bool IncludeVectors { get; init; } = false;
    public bool IncludeTotalCount { get; init; } = false;
}
```

### Sparse Vector based hybrid search

```csharp
interface ISparseVectorizedHybridSearch<TRecord>
{
    Task<VectorSearchResults<TRecord>> SparseVectorizedHybridSearch<TVector, TSparseVector>(
        TVector vector,
        TSparseVector sparsevector,
        SparseVectorizedHybridSearchOptions options,
        CancellationToken cancellationToken);
}

class SparseVectorizedHybridSearchOptions
{
    // The name of the property to target the dense vector search against.
    public string? VectorPropertyName { get; init; }
    // The name of the property to target the sparse vector search against.
    public string? SparseVectorPropertyName { get; init; }

    public VectorSearchFilter? Filter { get; init; }
    public int Top { get; init; } = 3;
    public int Skip { get; init; } = 0;
    public bool IncludeVectors { get; init; } = false;
    public bool IncludeTotalCount { get; init; } = false;
}
```

### Keyword Vectorizable text based hybrid search

```csharp
interface IKeywordVectorizableHybridSearch<TRecord>
{
    Task<VectorSearchResults<TRecord>> KeywordVectorizableHybridSearch(
        string searchText,
        ICollection<string> keywords,
        KeywordVectorizableHybridSearchOptions options = default,
        CancellationToken cancellationToken = default);
}

class KeywordVectorizableHybridSearchOptions
{
    // The name of the property to target the dense vector search against.
    public string? VectorPropertyName { get; init; }
    // The name of the property to target the text search against.
    public string? FullTextPropertyName { get; init; }

    public VectorSearchFilter? Filter { get; init; }
    public int Top { get; init; } = 3;
    public int Skip { get; init; } = 0;
    public bool IncludeVectors { get; init; } = false;
    public bool IncludeTotalCount { get; init; } = false;
}
```

### Sparse Vector based Vectorizable text hybrid search

```csharp
interface ISparseVectorizableTextHybridSearch<TRecord>
{
    Task<VectorSearchResults<TRecord>> SparseVectorizableTextHybridSearch(
        string searchText,
        ICollection<string> keywords,
        SparseVectorizableTextHybridSearchOptions options = default,
        CancellationToken cancellationToken = default);
}

class SparseVectorizableTextHybridSearchOptions
{
    // The name of the property to target the dense vector search against.
    public string? VectorPropertyName { get; init; }
    // The name of the property to target the sparse vector search against.
    public string? SparseVectorPropertyName { get; init; }

    public VectorSearchFilter? Filter { get; init; }
    public int Top { get; init; } = 3;
    public int Skip { get; init; } = 0;
    public bool IncludeVectors { get; init; } = false;
    public bool IncludeTotalCount { get; init; } = false;
}
```

## Decision Drivers

- Support for generating sparse vectors is required to make sparse vector based hybrid search viable.
- Multiple vectors per record scenarios need to be supported.
- No database in our evaluation set have been identified as supporting converting text to sparse vectors in the database on upsert and storing those sparse vectors in a retrievable field. Of course some of these DBs may use sparse vectors internally to implement keyword search, without exposing them to the caller.

## Scoping Considered Options

### 1. Keyword Hybrid Search Only

Only implement KeywordVectorizedHybridSearch & KeywordVectorizableTextHybridSearch for now, until
we can add support for generating sparse vectors.

### 2. Keyword and SparseVectorized Hybrid Search

Implement KeywordVectorizedHybridSearch & KeywordVectorizableTextHybridSearch but only
KeywordVectorizableTextHybridSearch, since no database in our evaluation set supports generating sparse vectors in the database.
This will require us to produce code that can generate sparse vectors from text.

### 3. All abovementioned Hybrid Search

Create all four interfaces and implement an implementation of SparseVectorizableTextHybridSearch that
generates the sparse vector in the client code.
This will require us to produce code that can generate sparse vectors from text.

### 4. Generalized Hybrid Search

Some databases support a more generalized version of hybrid search, where you can take two (or sometimes more) searches of any type and combine the results of these using your chosen fusion method.
You can implement Vector + Keyword search using this more generalized search.
For databases that support only Vector + Keyword hybrid search though, it is not possible to implement the generalized hybrid search on top of those databases.

## PropertyName Naming Considered Options

### 1. Explicit Dense naming

DenseVectorPropertyName
SparseVectorPropertyName

DenseVectorPropertyName
FullTextPropertyName

- Pros: This is more explicit, considering that there are also sparse vectors involved.
- Cons: It is inconsistent with the naming in the non-hybrid vector search.

### 2. Implicit Dense naming

VectorPropertyName
SparseVectorPropertyName

VectorPropertyName
FullTextPropertyName

- Pros: This is consistent with the naming in the non-hybrid vector search.
- Cons: It is internally inconsistent, i.e. we have sparse vector, but for dense it's just vector.

## Keyword splitting Considered Options

### 1. Accept Split keywords in interface

Accept an ICollection of string where each value is a separate keyword.
A version that takes a single keyword and calls the `ICollection<string>` version can also be provided as an extension method.

```csharp
    Task<VectorSearchResults<TRecord>> KeywordVectorizedHybridSearch(
        TVector vector,
        ICollection<string> keywords,
        KeywordVectorizedHybridSearchOptions options,
        CancellationToken cancellationToken);
```

- Pros: Easier to use in the connector if the underlying DB requires split keywords
- Pros: Only solution broadly supported, see comparison table above.

### 2. Accept single string in interface

Accept a single string containing all the keywords.

```csharp
    Task<VectorSearchResults<TRecord>> KeywordVectorizedHybridSearch(
        TVector vector,
        string keywords,
        KeywordVectorizedHybridSearchOptions options,
        CancellationToken cancellationToken);
```

- Pros: Easier for a user to use, since they don't need to do any keyword splitting.
- Cons: We don't have the capabilities to properly sanitise the string, e.g. splitting words appropriately for the language, and potentially removing filler words.

### 3. Accept either in interface

Accept either option and either combine or split the keywords in the connector as needed by the underlying db.

```csharp
    Task<VectorSearchResults<TRecord>> KeywordVectorizedHybridSearch(
        TVector vector,
        ICollection<string> keywords,
        KeywordVectorizedHybridSearchOptions options,
        CancellationToken cancellationToken);
    Task<VectorSearchResults<TRecord>> KeywordVectorizedHybridSearch(
        TVector vector,
        string keywords,
        KeywordVectorizedHybridSearchOptions options,
        CancellationToken cancellationToken);
```

- Pros: Easier for a user to use, since they can pick whichever suits them better
- Cons: We have to still convert to/from the internal presentation by either combining keywords or splitting them.
- Cons: We don't have the capabilities to properly sanitise the single string, e.g. splitting words appropriately for the language, and potentially removing filler words.

### 4. Accept either in interface but throw for not supported

Accept either option but throw for the one not supported by the underlying DB.

- Pros: Easier for us to implement.
- Cons: Harder for users to use.

### 5. Separate interfaces for each

Create a separate interface for the Enumerable and single string options, and only implement the one that is supported by the underlying system for each db.

- Pros: Easier for us to implement.
- Cons: Harder for users to use.

## Full text search index mandatory configuration Considered Options

Cosmos DB NoSQL requires a language to be specified when creating a full text search index.
Other DBs have optional values that can be set.

### 1. Pass option in via collection options

This option does the minimum by just adding a language option to the collection's options class.
This language would then be used for all full text search indexes created by the collection.

- Pros: Simplest to implement
- Cons: Doesn't allow multiple languages to be used for different fields in one record
- Cons: Doesn't add support for all full text search options for all dbs

### 2. Add extensions for RecordDefinition and data model Attributes

Add a property bag to the VectorStoreRecordProperty allowing database specific metadata to be provided.
Add an abstract base attribute that can be inherited from that allows extra metadata to be added to the data model,
where each database has their own attributes to specify their settings, with a method to convert the contents to
the property bag required by VectorStoreRecordProperty.

- Pros: Allows multiple languages to be used for different fields in one record
- Pros: Allows other DBs to add their own settings via their own attributes
- Cons: More work to implement

## Decision Outcome

### Scoping

Chosen option "1. Keyword Hybrid Search Only", since enterprise support for generating sparse vectors is poor and without an end to end story, the value is low.

### PropertyName Naming

Chosen option "2. Implicit Dense naming", since it is consistent with the existing vector search options naming.

### Keyword splitting

Chosen option "1. Accept Split keywords in interface", since it is the only one with broad support amongst databases.
