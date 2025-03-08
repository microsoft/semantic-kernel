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
    public VectorSearchFilter? Filter { get; init; } = new VectorSearchFilter();
    public string? VectorFieldName { get; init; }
    public int Limit { get; init; } = 3;
    public int Offset { get; init; } = 0;
    public bool IncludeVectors { get; init; } = false;
}

// Options for hybrid vector search.
public sealed class HybridVectorSearchOptions
{
    public static HybridVectorSearchOptions Default { get; } = new HybridVectorSearchOptions();
    public VectorSearchFilter? Filter { get; init; } = new VectorSearchFilter();
    public string? VectorFieldName { get; init; }
    public int Limit { get; init; } = 3;
    public int Offset { get; init; } = 0;
    public bool IncludeVectors { get; init; } = false;

    public string? HybridFieldName { get; init; }
}
```

To simplify calling search, without needing to call CreateQuery we can use extension methods.
e.g. Instead of `SearchAsync(VectorSearchQuery.CreateQuery(vector))` you can call `SearchAsync(vector)`

```csharp
public static class VectorSearchExtensions
{
    public static IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TRecord, TVector>(
        this IVectorSearch<TRecord> search,
        TVector vector,
        VectorSearchOptions? options = default,
        CancellationToken cancellationToken = default)
        where TRecord : class
    {
        return search.SearchAsync(new VectorizedSearchQuery<TVector>(vector, options), cancellationToken);
    }

    public static IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TRecord>(
        this IVectorSearch<TRecord> search,
        string searchText,
        VectorSearchOptions? options = default,
        CancellationToken cancellationToken = default)
        where TRecord : class
    {
        return search.SearchAsync(new VectorizableTextSearchQuery(searchText, options), cancellationToken);
    }

    // etc...
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
    var filter = new BasicVectorSearchFilter().EqualTo(nameof(Glossary.Category), "Core Definitions");
    searchResults = vectorSearch.SearchAsync(
        VectorSearchQuery.CreateQuery(
            searchEmbedding,
            new()
            {
                Filter = filter,
                VectorFieldName = nameof(Glossary.DefinitionEmbedding)
            }));
}
```

## Options considered

### Option 1: Search object

See the [Interface](#interface) section above for a description of this option.

Pros:

- It can support multiple query types, each with different options.
- It is easy to add more query types in future without it being a breaking change.

Cons:

- Any query type that isn't supported by a connector implementation will cause an exception to be thrown.

### Option 2: Vector only

The abstraction will only support the most basic functionality and all other functionality is supported on the concrete implementation.
E.g. Some vector databases do not support generating embeddings in the service, so the connector would not support `VectorizableTextSearchQuery` from option 1.

Pros:

- The user doesn't need to know which query types are supported by which vector store connector types.

Cons:

- Only allows searching by vectors in the abstraction which is a very low common denominator.

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

### Option 3: Abstract base class

One of the main requirements is to allow future extensibility with additional query types.
One way to achieve this is to use an abstract base class that can auto implement new methods
that throw with NotSupported unless overridden by each implementation. This behavior would
be similar to Option 1. With Option 1 though, the same behavior is achieved via extension methods.
The set of methods end up being the same with Option 1 and Option 3, except that Option 1 also has
a Search method that takes `VectorSearchQuery` as input.

`IVectorSearch` is a separate interface to `IVectorStoreRecordCollection`, but the intention is
for `IVectorStoreRecordCollection` to inherit from `IVectorSearch`.

This means that some (most) implementations of `IVectorSearch` will be part of `IVectorStoreRecordCollection` implementations.
We anticipate cases where we need to support standalone `IVectorSearch` implementations where the store supports search
but isn't necessarily writable.

Therefore a hierarchy of abstract base classes would be required.

We also considered default interface methods, but there is no support in .net Framework for this, and SK has to support .net Framework.

Pros:

- It can support multiple query types, each with different options.
- It is easy to add more query types in future without it being a breaking change.
- Allows different return types for each search type.

Cons:

- Any query type that isn't supported by a connector implementation will cause an exception to be thrown.
- Doesn't support multiple inheritance, so where multiple key types need to be supported this doesn't work.
- Doesn't support multiple inheritance, so any additional functionality that needs to be added to `VectorStoreRecordCollection`, won't be possible to be added using a similar mechanism.

```csharp
abstract class BaseVectorSearch<TRecord>
    where TRecord : class
{
    public virtual IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TVector>(
        this IVectorSearch<TRecord> search,
        TVector vector,
        VectorSearchOptions? options = default,
        CancellationToken cancellationToken = default)
    {
        throw new NotSupportedException($"Vectorized search is not supported by the {this._connectorName} connector");
    }

    public virtual IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync(
        this IVectorSearch<TRecord> search,
        string searchText,
        VectorSearchOptions? options = default,
        CancellationToken cancellationToken = default)
    {
        throw new NotSupportedException($"Vectorizable text search is not supported by the {this._connectorName} connector");
    }
}

abstract class BaseVectorStoreRecordCollection<TKey, TRecord> : BaseVectorSearch<TRecord>
{
    public virtual async Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        if (!await this.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
        {
            await this.CreateCollectionAsync(cancellationToken).ConfigureAwait(false);
        }
    }
}

// We support multiple types of keys here, but we cannot inherit from multiple base classes.
class QdrantVectorStoreRecordCollection<TRecord> : BaseVectorStoreRecordCollection<ulong, TRecord> : BaseVectorStoreRecordCollection<Guid, TRecord>
{
}
```

### Option 4: Interface per search type

One of the main requirements is to allow future extensibility with additional query types.
One way to achieve this is to add additional interfaces as implementations support additional functionality.

Pros:

- Allows different implementations to support different search types without needing to throw exceptions for not supported functionality.
- Allows different return types for each search type.

Cons:

- Users will still need to know which interfaces are implemented by each implementation to cast to those as necessary.
- We will not be able to add more Search functionality to `IVectorStoreRecordCollection` over time, since it would be a breaking change. Therefore, a user that has an instance of `IVectorStoreRecordCollection`, but wants to e.g. do a hybrid search, will need to cast to `IHybridTextVectorizedSearch` first before being able to search.

```csharp

// Vector search using vector.
interface IVectorizedSearch<TRecord>
{
    IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TVector>(
        TVector vector,
        VectorSearchOptions? searchOptions);
}

// Vector search using query text that will be vectorized downstream.
interface IVectorizableTextSearch<TRecord>
{
    IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TVector>(
        string queryText,
        VectorSearchOptions? searchOptions);
}

// Hybrid search using a vector and a text portion that will be used for a keyword search.
interface IHybridTextVectorizedSearch<TRecord>
{
    IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TVector>(
        TVector vector,
        string queryText,
        HybridVectorSearchOptions? searchOptions);
}

// Hybrid search using text that will be vectorized downstream and also used for a keyword search.
interface IHybridVectorizableTextSearch<TRecord>
{
    IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TVector>(
    string queryText,
    HybridVectorSearchOptions? searchOptions);
}

class AzureAISearchVectorStoreRecordCollection<TRecord>: IVectorStoreRecordCollection<string, TRecord>, IVectorizedSearch<TRecord>, IVectorizableTextSearch<TRecord>
{
}

```

## Decision Outcome

Chosen option: 4

The consensus is that option 4 is easier to understand for users, where only functionality that works for all vector stores are exposed by default.
