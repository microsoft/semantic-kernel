---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: Krzysztof318
date: 2024-03-02
deciders: ???
consulted: ???
informed: ???
---

# Embeddings Generation in Semantic Kernel

## Context and Problem Statement

### General Information

The current abstraction of generating embeddings has generic interface which potentially can be used for generation from multi-modal data.
It's good because we want to enable the generation of embeddings from different types of data, such as text, images and others.

We also want to make it possible to parameterize the query and return metadata but this is not possible in the current abstraction.

### Embeddings models

OpenAI provides models that allow for generating embeddings only from textual data.\
These models return metadata, and also allow for parameterizing the query.

Google VertexAI provides models that allow for generating embeddings from textual data, as well as from images and other types of data.
These models return metadata, and also allow for parameterizing the query.

<!-- This is an optional element. Feel free to remove. -->

## Decision Drivers

1. Abstraction should be able to generate embeddings from different types of data, at least from text and images.
2. Abstraction should return metadata with generated embeddings.
3. Abstraction should allow parameterize the embeddings query.
4. We should maintain the precision of the obtained embeddings.

## Considered Options

### Option 1 [Current] - Generic embeddings generation interface and specialized interfaces for different types of data

The current abstraction of generating embeddings only allows for generation from text and image data.\
We return raw data in the form of `IList<ReadOnlyMemory<TEmbedding>>` instead of a specialized data type like `IList<EmbeddingContent>`.

In this option, we cannot parameterize the query or return metadata.

```csharp
public interface IEmbeddingGenerationService<TValue, TEmbedding> : IAIService where TEmbedding : unmanaged
{
    Task<IList<ReadOnlyMemory<TEmbedding>>> GenerateEmbeddingsAsync(
        IList<TValue> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default);
}

public interface ITextEmbeddingGenerationService : IEmbeddingGenerationService<string, float> { }

public interface IImageEmbeddingGenerationService : IEmbeddingGenerationService<ImageContent, float> { }
```

Pros:
- Allows for generating embeddings from different types of data.
- Generic interface.
- Interface segregation.

Cons:
- Cannot parameterize the query.
- Cannot return metadata.
- We lost precision.

### Option 2 [Proposed] - Specialized embeddings generation interfaces for different types of data with metadata and query parameterization without a generic interface

This option allows you to generate embeds from different data types, such as text and images.\
And allows you to parameterize the query and return metadata.\
We can also develop interfaces with other returned types like `EmbeddingContent<int>`, `EmbeddingContent<double>`, etc.

```csharp
public class EmbeddingContent<TEmbedding> : KernelContent where TEmbedding : unmanaged
{
    public EmbeddingContent(
        ReadOnlyMemory<TEmbedding> data,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.Data = data;
    }

    public IReadOnlyMemory<TEmbedding> Data { get; set; }
}

public interface ITextEmbeddingGenerationService : IAIService
{
    Task<IReadOnlyList<EmbeddingContent<double>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel = null,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default);
}

public interface IImageEmbeddingGenerationService : IAIService
{
    Task<IReadOnlyList<EmbeddingContent<double>>> GenerateEmbeddingsAsync(
        IList<ImageContent> data,
        Kernel? kernel = null,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default);
}
```
Pros:
- Allows for generating embeddings from different types of data.
- Allows for parameterizing the query.
- Allows for returning metadata.
- Interface segregation.

Cons:
- No generic interface.

### Option 3 [Proposed] - Common interface for embeddings generation with metadata and query parameterization

Similar to option 2, but with a common interface for generating embeddings from different types of data.

```csharp
public class EmbeddingContent<TEmbedding> : KernelContent where TEmbedding : unmanaged
{
    public EmbeddingContent(
        ReadOnlyMemory<TEmbedding> data,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.Data = data;
    }

    public ReadOnlyMemory<TEmbedding> Data { get; set; }
}

public interface IEmbeddingGenerationService : IAIService
{
    Task<IReadOnlyList<EmbeddingContent<double>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel = null,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default);
    
    Task<IReadOnlyList<EmbeddingContent<double>>> GenerateEmbeddingsAsync(
        IList<ImageContent> data,
        Kernel? kernel = null,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default);
}
```

Pros:
- Allows for generating embeddings from different types of data.
- Allows for parameterizing the query.
- Allows for returning metadata.

Cons:
- No generic interface.
- One common interface for different types of data. Many models don't support all types of data.

### Option 4 [Proposed] - One interface for embeddings generation with metadata and query parameters

Similar to option 3 but with only one method with KernelContent param and non-generic EmbeddingContent.

```csharp
public class EmbeddingContent : KernelContent
{
    public EmbeddingContent(
        ReadOnlyMemory<double> data,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.Data = data;
    }

    public ReadOnlyMemory<double> Data { get; set; }
}

public interface IEmbeddingGenerationService : IAIService
{
    Task<IReadOnlyList<EmbeddingContent>> GenerateEmbeddingsAsync(
        IList<KernelContent> data,
        Kernel? kernel = null,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = null);

    IList<Type> SupportedContents { get; }
}
```

Pros:
- Simplicity.
- We reusing existing KernelContent descants.
- Allows for generating embeddings from different types of data.
- Allows for parameterizing the query.
- Allows for returning metadata.

Cons:
- No generic interface.
- We cannot return embeddings with different types.
- Exception would be thrown for not supported contents. Many models don't support all types of data.

### Option 5 [Proposed] - Generic embeddings generation interface with metadata and execution parameters

Similar to Option 1 but with EmbeddingContent, metadata and execution settings.

Abstraction:
```csharp
public interface IEmbeddingGenerationService<TValue, TEmbedding> : IAIService
        where TEmbedding : unmanaged,
              TValue : KernelContent
{
    Task<IReadOnlyList<EmbeddingContent<TEmbedding>>> GenerateEmbeddingsAsync(
        IList<TValue> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default);
}

public class EmbeddingContent<TEmbedding>
        : KernelContent where TEmbedding : unmanaged
{
    public EmbeddingContent(
        ReadOnlyMemory<TEmbedding> data,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.Data = data;
    }

    public ReadOnlyMemory<TEmbedding> Data { get; set; }
}
```
Sample implementation:
```csharp
public class EmbeddingGenerationService
        : IEmbeddingGenerationService<TextContent, float>,
          IEmbeddingGenerationService<ImageContet, double>
{
    public Task<IReadOnlyList<EmbeddingContent<float>>> GenerateEmbeddingsAsync(
        IList<TextContent> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default) { /* implementation */ }

    public Task<IReadOnlyList<EmbeddingContent<double>>> GenerateEmbeddingsAsync(
        IList<ImageContet> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default) { /* implementation */ }
}
```

Pros:
- We reusing existing KernelContent descants, because TValue is limited to KernelContent and derived types.
- Allows for generating embeddings from different types of data.
- Allows returning data with different types like float, double etc.
- Allows for parameterizing the query.
- Allows for returning metadata.

Cons:
- More complex than option 4.

## Decision Outcome

Chosen option: "{title of option 1}", because
{justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force {force} | … | comes out best (see below)}.

<!-- This is an optional element. Feel free to remove. -->

### Consequences

- Good, because {positive consequence, e.g., improvement of one or more desired qualities, …}
- Bad, because {negative consequence, e.g., compromising one or more desired qualities, …}
- … <!-- numbers of consequences can vary -->

<!-- This is an optional element. Feel free to remove. -->

## More Information

{You might want to provide additional evidence/confidence for the decision outcome here and/or
document the team agreement on the decision and/or
define when this decision when and how the decision should be realized and if/when it should be re-visited and/or
how the decision is validated.
Links to other decisions and resources might appear here as well.}
