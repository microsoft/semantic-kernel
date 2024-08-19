---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: westey-m
date: 2024-08-14
deciders: sergeymenshykh, markwallace, rbarreto, dmytrostruk, westey-m, matthewbolanos, eavanvalkenburg
consulted: stephentoub, dluc, ajcvickers, roji
informed: 
---

# Updated Vector Search Design

## Requirements

1. Support searching by Vector.
1. Support Vectors with different types of elements and allow extensibility to support new types of vector in future (e.g. sparse).
1. Support searching by Text. This is required to support the scenario where the service does the embedding generation or the scenario where the embedding generation is done in the pipeline.
1. Allow extensibility to search by other modalities, e.g. image.
1. Allow extensibility to do hybrid search.
1. Allow basic filtering with possibility to extend in future.
1. Provide extension methods to simplify search experience.

## Interface

The vector search interface takes a `VectorSearchQuery` object. This object is an abstract base class that has various subclasses
representing different types of search.

```csharp
interface IVectorSearch<TRecord>
{
    IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync(
        VectorSearchQuery vectorQuery,
        CancellationToken cancellationToken = default);
}
```

Each `VectorSearchQuery` subclass represents a specific type of search.
The possible variations are restricted by the fact that `VectorSearchQuery` and all subclasses have internal constructors.
Therefore, a developer cannot create a custom search query type and expect it to be executable by `IVectorSearch.SearchAsync`.
Having subclasses in this way though, allows each query to have different parameters and options.

```csharp
// Base class for all vector search queries.
abstract class VectorSearchQuery(
    string queryType,
    object? searchOptions)
{
    public static VectorizedSearchQuery<TVector> CreateQuery<TVector>(TVector vector, VectorSearchOptions? options = default) => new(vector, options);
    public static VectorizableTextSearchQuery CreateQuery(string text, VectorSearchOptions? options = default) => new(text, options);

    // Showing future extensibility possibilities.
    public static HybridTextVectorizedSearchQuery<TVector> CreateHybridQuery<TVector>(TVector vector, string text, HybridVectorSearchOptions? options = default) => new(vector, text, options);
    public static HybridVectorizableTextSearchQuery CreateHybridQuery(string text, HybridVectorSearchOptions? options = default) => new(text, options);
}

// Vector search using vector.
class VectorizedSearchQuery<TVector>(
    TVector vector,
    VectorSearchOptions? searchOptions) : VectorSearchQuery;

// Vector search using query text that will be vectorized downstream.
class VectorizableTextSearchQuery(
    string queryText,
    VectorSearchOptions? searchOptions) : VectorSearchQuery;

// Hybrid search using a vector and a text portion that will be used for a keyword search.
class HybridTextVectorizedSearchQuery<TVector>(
    TVector vector,
    string queryText,
    HybridVectorSearchOptions? searchOptions) : VectorSearchQuery;

// Hybrid search using text that will be vectorized downstream and also used for a keyword search.
class HybridVectorizableTextSearchQuery(
    string queryText,
    HybridVectorSearchOptions? searchOptions) : VectorSearchQuery

// Options for basic vector search.
public class VectorSearchOptions
{
    public static VectorSearchOptions Default { get; } = new VectorSearchOptions();
    public BasicVectorSearchFilter? BasicVectorSearchFilter { get; init; } = new BasicVectorSearchFilter();
    public string? VectorFieldName { get; init; }
    public int Limit { get; init; } = 3;
    public int Offset { get; init; } = 0;
    public bool IncludeVectors { get; init; } = false;
}

// Options for hybrid vector search.
public sealed class HybridVectorSearchOptions
{
    public static HybridVectorSearchOptions Default { get; } = new HybridVectorSearchOptions();
    public BasicVectorSearchFilter? BasicVectorSearchFilter { get; init; } = new BasicVectorSearchFilter();
    public string? VectorFieldName { get; init; }
    public int Limit { get; init; } = 3;
    public int Offset { get; init; } = 0;
    public bool IncludeVectors { get; init; } = false;

    public string? HybridFieldName { get; init; }
}
```

## Usage Examples

```csharp
public sealed class Glossary
{
    [VectorStoreRecordKey]
    public ulong Key { get; set; }
    [VectorStoreRecordData]
    public string Category { get; set; }
    [VectorStoreRecordData]
    public string Term { get; set; }
    [VectorStoreRecordData]
    public string Definition { get; set; }
    [VectorStoreRecordVector(1536)]
    public ReadOnlyMemory<float> DefinitionEmbedding { get; set; }
}

public async Task VectorSearchAsync(IVectorSearch<Glossary> vectorSearch)
{
    var searchEmbedding = new ReadOnlyMemory<float>(new float[1536]);

    // Vector search.
    var searchResults = vectorSearch.SearchAsync(VectorSearchQuery.CreateQuery(searchEmbedding));
    searchResults = vectorSearch.SearchAsync(searchEmbedding); // Extension method.

    // Vector search with specific vector field.
    searchResults = vectorSearch.SearchAsync(VectorSearchQuery.CreateQuery(searchEmbedding, new() { VectorFieldName = nameof(Glossary.DefinitionEmbedding) }));
    searchResults = vectorSearch.SearchAsync(searchEmbedding, new() { VectorFieldName = nameof(Glossary.DefinitionEmbedding) }); // Extension method.

    // Text vector search.
    searchResults = vectorSearch.SearchAsync(VectorSearchQuery.CreateQuery("What does Semantic Kernel mean?"));
    searchResults = vectorSearch.SearchAsync("What does Semantic Kernel mean?"); // Extension method.

    // Text vector search with specific vector field.
    searchResults = vectorSearch.SearchAsync(VectorSearchQuery.CreateQuery("What does Semantic Kernel mean?", new() { VectorFieldName = nameof(Glossary.DefinitionEmbedding) }));
    searchResults = vectorSearch.SearchAsync("What does Semantic Kernel mean?", new() { VectorFieldName = nameof(Glossary.DefinitionEmbedding) }); // Extension method.

    // Hybrid vector search.
    searchResults = vectorSearch.SearchAsync(VectorSearchQuery.CreateHybridQuery(searchEmbedding, "What does Semantic Kernel mean?", new() { HybridFieldName = nameof(Glossary.Definition) }));
    searchResults = vectorSearch.HybridVectorizedTextSearchAsync(searchEmbedding, "What does Semantic Kernel mean?", new() { HybridFieldName = nameof(Glossary.Definition) }); // Extension method.

    // Hybrid text vector search with field names specified for both vector and keyword search.
    searchResults = vectorSearch.SearchAsync(VectorSearchQuery.CreateHybridQuery("What does Semantic Kernel mean?", new() { VectorFieldName = nameof(Glossary.DefinitionEmbedding), HybridFieldName = nameof(Glossary.Definition) }));
    searchResults = vectorSearch.HybridVectorizableTextSearchAsync("What does Semantic Kernel mean?", new() { VectorFieldName = nameof(Glossary.DefinitionEmbedding), HybridFieldName = nameof(Glossary.Definition) }); // Extension method.

    // In future we can also support images or other modalities, e.g.
    IVectorSearch<Images> imageVectorSearch = ...
    searchResults = imageVectorSearch.SearchAsync(VectorSearchQuery.CreateBase64EncodedImageQuery(base64EncodedImageString, new() { VectorFieldName = nameof(Images.ImageEmbedding) }));

    // Vector search with filtering.
    var filter = new BasicVectorSearchFilter().Equality(nameof(Glossary.Category), "Core Definitions");
    searchResults = vectorSearch.SearchAsync(
        VectorSearchQuery.CreateQuery(
            searchEmbedding,
            new()
            {
                BasicVectorSearchFilter = filter,
                VectorFieldName = nameof(Glossary.DefinitionEmbedding)
            }));
}
```

## Options considered

### Option 1: Search object

See the [Interface](#interface) section above for a description of this option.

The benefit is that it can support multiple query types, each with different options.
It's easy to add more query types in future without it being a breaking change.

The drawback of this option is that any query type that isn't supported by a connector
implementation will cause an exception to be thrown.

### Option 2: Vector only

Only allow searching by vectors in the abstraction.

The benefit is that the user doesn't need to know which query types are supported by which vector store connector types.
E.g. Some vector databases do not support generating embeddings in the service, so the connector would not support `VectorizableTextSearchQuery` from option 1.
The connector will therefore throw when the user calls it with such a query, unless we layer an embedding decorator on top of the connector, which generates
an embedding automatically on the client side.

The drawback of this option is that the abstraction does not support this scenario where a vector search is done using text that will be vectorized in the service.
Adding support for this later would be a breaking change.

```csharp
interface IVectorSearch<TRecord>
{
    IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TVector>(
        TVector vector,
        VectorSearchOptions? searchOptions
        CancellationToken cancellationToken = default);
}

class AzureAISearchVectorStoreRecordCollection<TRecord> : IVectorSearch<TRecord>
{
    public IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TVector>(
        TVector vector,
        VectorSearchOptions? searchOptions
        CancellationToken cancellationToken = default);

    public IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync(
        string queryText,
        VectorSearchOptions? searchOptions
        CancellationToken cancellationToken = default);
}
```

## Decision Outcome

Chosen option: 1: Search Object, because
it allows more future extensibility without breaking changes and makes it easier to implement the current requirements.
