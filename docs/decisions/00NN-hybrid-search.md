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
|Hybrid search supported|Y|Y|N (No parallel execution with fusion)|N|Y||Y|Y|Y|Y|Y|
|Hybrid search definition|Vector + FullText|[Vector + Keyword (BM25F)](https://weaviate.io/developers/weaviate/search/hybrid)|||[Vector + Sparse Vector for keywords](https://docs.pinecone.io/guides/get-started/key-features#hybrid-search)||[Vector + SparseVector / Keyword](https://qdrant.tech/documentation/concepts/hybrid-queries/)|[Vector + SparseVector](https://milvus.io/docs/multi-vector-search.md)|Vector + FullText|[Vector + Fulltext (BM25)](https://learn.microsoft.com/en-us/azure/cosmos-db/gen-ai/hybrid-search)|[Vector + FullText](https://www.mongodb.com/docs/atlas/atlas-search/tutorial/hybrid-search)|
|Fusion method configurable|N|Y|||?||Y|Y|Y, but only one option|Y, but only one option|N|
|Fusion methods|[RRF](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking)|Ranked/RelativeScore|||?||RRF / DBSF|[RRF / Weighted](https://milvus.io/docs/multi-vector-search.md)|[RRF](https://www.elastic.co/search-labs/tutorials/search-tutorial/vector-search/hybrid-search)|[RRF](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/query/rrf)|[RRF](https://www.mongodb.com/docs/atlas/atlas-search/tutorial/hybrid-search)|
|Hybrid Search Input Params|Vector + string|[Vector + string](https://weaviate.io/developers/weaviate/api/graphql/search-operators#hybrid)|||Vector + SparseVector||[Vector + SparseVector](https://qdrant.tech/documentation/concepts/hybrid-queries/)|[Vector + SparseVector](https://milvus.io/docs/multi-vector-search.md)|Vector + string|Vector + string array|Vector + string|
|Sparse Distance Function|n/a|n/a|||[dotproduct only for both dense and sparse, 1 setting for both](https://docs.pinecone.io/guides/data/understanding-hybrid-search#sparse-dense-workflow)||dotproduct|Inner Product|n/a|n/a|n/a|
|Sparse Indexing options|n/a|n/a|||no separate config to dense||ondisk / inmemory  + IDF|[SPARSE_INVERTED_INDEX / SPARSE_WAND](https://milvus.io/docs/index.md?tab=sparse)|n/a|n/a|n/a|
|Sparse data model|n/a|n/a|||[indices & values arrays](https://docs.pinecone.io/guides/data/upsert-sparse-dense-vectors)||indices & values arrays|[sparse matrix / List of dict / list of tuples](https://milvus.io/docs/sparse_vector.md#Use-sparse-vectors-in-Milvus)|n/a|n/a|n/a|
|Reranking supported|[Yes](https://learn.microsoft.com/en-us/azure/search/semantic-search-overview)|-|-|-|-|-|-|-|-|-|-|

Glossary:

- RRF = Reciprical Rank Fusion
- DBSF = Distribution-Based Score Fusion
- IDF = Inverse Document Frequency

### Naming

|Name|Parameters|Keyword Property Selector|Dense Vector Property Selector|
|-|-|-|-|
|KeywordVectorizedHybridSearch|string + Dense Vector|TextPropertyName|DenseVectorPropertyName|
|SparseVectorizedHybridSearch|Sparse Vector + Dense Vector|SparseVectorPropertyName|DenseVectorPropertyName|
|KeywordVectorizableTextHybridSearch|string + string / string|TextPropertyName|DenseVectorPropertyName|
|SparseVectorizableTextHybridSearch|string + string / string|SparseVectorPropertyName|DenseVectorPropertyName|

### Keyword based hybrid search

```csharp
interface IKeywordVectorizedHybridSearch<TRecord>
{
    Task<VectorSearchResults<TRecord>> KeywordVectorizedHybridSearch(
        TVector vector,
        string keywords,
        KeywordVectorizedHybridSearchOptions options,
        CancellationToken cancellationToken);
}

class KeywordVectorizedHybridSearchOptions
{
    // The name of the property to target the vector search against.
    public string? DenseVectorPropertyName { get; init; }
    // The name of the property to target the text search against.
    public string? TextPropertyName { get; init; }
    // Allow fusion method to be configurable for dbs that support configuration. If null, a default is used.
    public string FusionMethod { get; init; } = null;

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
    Task<VectorSearchResults<TRecord>> SparseVectorizedHybridSearch(
        TVector denseVector,
        TVector sparsevector,
        SparseVectorizedHybridSearchOptions options,
        CancellationToken cancellationToken);
}

class SparseVectorizedHybridSearchOptions
{
    // The name of the property to target the dense vector search against.
    public string? DenseVectorPropertyName { get; init; }
    // The name of the property to target the sparse vector search against.
    public string? SparseVectorPropertyName { get; init; }
    // Allow fusion method to be configurable for dbs that support configuration. If null, a default is used.
    public string FusionMethod { get; init; } = null;

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
        string description,
        string? keywords = default,
        KeywordVectorizableHybridSearchOptions options = default,
        CancellationToken cancellationToken = default);
}

class KeywordVectorizableHybridSearchOptions
{
    // The name of the property to target the dense vector search against.
    public string? DenseVectorPropertyName { get; init; }
    // The name of the property to target the text search against.
    public string? TextPropertyName { get; init; }
    // Allow fusion method to be configurable for dbs that support configuration. If null, a default is used.
    public string FusionMethod { get; init; } = null;

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
        string description,
        string? keywords = default,
        SparseVectorizableTextHybridSearchOptions options = default,
        CancellationToken cancellationToken = default);
}

class SparseVectorizableTextHybridSearchOptions
{
    // The name of the property to target the dense vector search against.
    public string? DenseVectorPropertyName { get; init; }
    // The name of the property to target the sparse vector search against.
    public string? SparseVectorPropertyName { get; init; }
    // Allow fusion method to be configurable for dbs that support configuration. If null, a default is used.
    public string FusionMethod { get; init; } = null;

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
- No database in our evaluation set have been identified as supporting generating sparse vectors in the database.

## Scoping Considered Options

### 1. Keyword Hybrid Search Only

Only implement KeywordVectorizedHybridSearch & KeywordVectorizableTextHybridSearch for now, until
we can add support for generating sparse vectors.

### 2. Keyword and SparseVectorized Hybrid Search

Implement KeywordVectorizedHybridSearch & KeywordVectorizableTextHybridSearch but only
KeywordVectorizableTextHybridSearch, since no database in our evaluation set supports generating sparse vectors in the database.
This will require us to produce code that can generate sparse vectors from text.

### 3. All Hybrid Search

Create all four interfaces and implement an implementation of SparseVectorizableTextHybridSearch that
generates the sparse vector in the client code.
This will require us to produce code that can generate sparse vectors from text.

## PropertyName Naming Considered Options

### 1. Explicit Dense naming

DenseVectorPropertyName
SparseVectorPropertyName

DenseVectorPropertyName
TextPropertyName

Pros: This is more explicit, considering that there are also sparse vectors involved.
Cons: It is inconsistent with the naming in the non-hybrid vector search.

### 2. Implicit Dense naming

VectorPropertyName
SparseVectorPropertyName

VectorPropertyName
TextPropertyName

Pros: This is consistent with the naming in the non-hybrid vector search.
Cons: It is internally inconsistent, i.e. we have sparse vector, but for dense it's just vector.

## Keyword splitting Considered Options

### 1. Accept Split keywords in interface

Accept an IEnumerable of string where each value is a separate keyword.

```csharp
    Task<VectorSearchResults<TRecord>> KeywordVectorizedHybridSearch(
        TVector vector,
        IEnumerable<string> keywords,
        KeywordVectorizedHybridSearchOptions options,
        CancellationToken cancellationToken);
```

Pros: Easier to use in the connector if the underlying DB requires split keywords

### 2. Accept single string in interface

Accept a single string containing all the keywords.

```csharp
    Task<VectorSearchResults<TRecord>> KeywordVectorizedHybridSearch(
        TVector vector,
        string keywords,
        KeywordVectorizedHybridSearchOptions options,
        CancellationToken cancellationToken);
```

Pros: Easier for a user to use, since they don't need to do any keyword splitting themselves.

### 3. Accept either in interface

Accept either option.

```csharp
    Task<VectorSearchResults<TRecord>> KeywordVectorizedHybridSearch(
        TVector vector,
        IEnumerable<string> keywords,
        KeywordVectorizedHybridSearchOptions options,
        CancellationToken cancellationToken);
    Task<VectorSearchResults<TRecord>> KeywordVectorizedHybridSearch(
        TVector vector,
        string keywords,
        KeywordVectorizedHybridSearchOptions options,
        CancellationToken cancellationToken);
```

Pros: Easier for a user to use, since they can pick whichever suits them better
Cons: We have to still convert to/from the internal presentation by either combining keywords or splitting them.

### 3. Accept either in interface but throw for not supported

Accept either option but throw for the one not supported by the underly DB.

Pros: Easier for us to implement.
Cons: Harder for users to use.

### 4. Separate interfaces for each

Create a separate interface for the Enumerable and single string options, and only implement the one that is supported by the underlying system for each db.

Pros: Easier for us to implement.
Cons: Harder for users to use.

## Decision Outcome

Chosen option: "{title of option 1}", because
{justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force {force} | � | comes out best (see below)}.
