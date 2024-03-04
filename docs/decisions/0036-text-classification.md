---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: Krzysztof318
date: 2024-03-03
deciders: ???
consulted: ???
informed: ???
---

# Classification models in Semantic Kernel

## Context and Problem Statement

### General Information

The purpose of this ADR is to standardize how classification models should be implemented.

### Problem

Classification models can be used to classify different types of data, such as text, images, etc.\
These models return a variety of data structures, making it hard to extract an abstraction. Below are examples of structures.

#### OpenAI

```json
{
  "id": "modr-XXXXX",
  "model": "text-moderation-007",
  "results": [
    {
      "flagged": true,
      "categories": {
        "sexual": false,
        "hate": false,
        "harassment": false,
        "self-harm": false,
        "sexual/minors": false,
        "hate/threatening": false,
        "violence/graphic": false,
        "self-harm/intent": false,
        "self-harm/instructions": false,
        "harassment/threatening": true,
        "violence": true
      },
      "category_scores": {
        "sexual": 1.2282071e-6,
        "hate": 0.010696256,
        "harassment": 0.29842457,
        "self-harm": 1.5236925e-8,
        "sexual/minors": 5.7246268e-8,
        "hate/threatening": 0.0060676364,
        "violence/graphic": 4.435014e-6,
        "self-harm/intent": 8.098441e-10,
        "self-harm/instructions": 2.8498655e-11,
        "harassment/threatening": 0.63055265,
        "violence": 0.99011886
      }
    }
  ]
}
```

#### HuggingFace interference API

```json
[
  [
    {
      "label": "disappointment",
      "score": 0.5044490694999695
    },
    {
      "label": "sadness",
      "score": 0.3469429612159729
    }
  ]
]
```

## Decision Drivers

If we decide to create a common abstraction for classification models, we should consider the following drivers:
1. Abstraction should be able to generate classification from different types of data, at least from text and images.
2. Abstraction should return metadata with generated classification results.
3. Abstraction should allow parameterize the classification query.

## Considered Options

### Option 1 [Proposed] - With abstraction

This option assumes the creation of a common abstraction layer for classification models.

Since the models return different data structures, we return `IReadOnlyDictionary<string, object?> Result` as a result.
This type is very abstract by which the consumer must know the structure of the result
and will probably have to use a cast to a connector-supplied type such like `OpenAIClassificationData`.
We could just as well return `object` and always require a casting.

```csharp
public interface ITextClassificationService : IAIService
{
    Task<IReadOnlyList<ClassifiedContent>> GetClassifiedContentsAsync(
        IEnumerable<TextContent> texts,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default);
}

public interface IImageClassificationService : IAIService
{
    Task<IReadOnlyList<ClassifiedContent>> GetClassifiedContentsAsync(
        IEnumerable<ImageContent> images,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default);
}

public class ClassifiedContent : KernelContent
{
    public ClassifiedContent(
        KernelContent classifiedContent,
        IReadOnlyDictionary<string, object?> result,
        object? innerContent = null,
        string? modelId = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.ClassifiedContent = classifiedContent;
        this.Result = result;
    }

    // value (double) will be used as score value and also as boolean 1|0 (true|false)
    public IReadOnlyDictionary<string, double> ScoredCategories { get; }
}
```

Pros:
- We have abstraction for classification models.

Cons:
- double used as decimal value and also as boolean

### Option 2 [Proposed] - With abstraction and common method

Similar to option 1 but with one method with kernelcontent param.

```csharp
public interface IClassificationService : IAIService
{
    Task<IReadOnlyList<ClassifiedContent>> GetClassifiedContentsAsync(
        IEnumerable<KernelContent> contents,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default);

    IList<Type> SupportedContents { get; }
}

public class ClassifiedContent : KernelContent
{
    public ClassifiedContent(
        KernelContent classifiedContent,
        IReadOnlyDictionary<string, object?> result,
        object? innerContent = null,
        string? modelId = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.ClassifiedContent = classifiedContent;
        this.Result = result;
    }

    // value (double) will be used as score value and also as boolean 1|0 (true|false)
    public IReadOnlyDictionary<string, double> ScoredCategories { get; }
}
```

Pros:
- Simplicity.
- We have abstraction for classification models.

Cons:
- Exception would be thrown if model doesn't support type of content.
- Double value used as decimal value and also as boolean

### Option 3 [Proposed] - Same as option 1 and 2 but with different ClassifiedContent

Same as option 1 and 2 but with different ClassifiedContent.ScoredCategories

```csharp
public class ClassifiedContent : KernelContent
{
    public ClassifiedContent(
        KernelContent classifiedContent,
        IReadOnlyDictionary<string, object?> result,
        object? innerContent = null,
        string? modelId = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.ClassifiedContent = classifiedContent;
        this.Result = result;
    }

    // bool used to indicate is category flagged, double for score value
    public IReadOnlyDictionary<string, (bool, double)> ScoredCategories { get; }
}
```

Pros:
- More readable than `IReadOnlyDictionary<string, double>`
- We have abstraction for classification models.

Cons:
- More complex
- Depending on the functionality of the model, double may always be 0 or bool be false.

### Option 4 [Proposed] - Without abstraction, only specialized implementations

This solution dispenses with abstractions altogether; it uses concrete implementations for each model.

As a sample we take OpenAI moderation endpoint.
```csharp
public class OpenAITextClassificationService : IAIService
{
    Task<IReadOnlyList<OpenAIClassifiedContent>> GetClassifiedContentsAsync(
        IEnumerable<TextContent> texts,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default) { }
}

public class OpenAIClassifiedContent : KernelContent
{
    public OpenAIClassifiedContent(
        KernelContent classifiedContent,
        IReadOnlyDictionary<string, object?> result,
        object? innerContent = null,
        string? modelId = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.ClassifiedContent = classifiedContent;
        this.Result = result;
    }

    public OpenAIClassificationData Result { get; }
}
```
Pros:
- We have a clear structure for the result.

Cons:
- We don't have a common abstraction for classification models.

## Decision Outcome

Chosen option: "{title of option 1}", because
{justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force {force} | … | comes
out best (see below)}.

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
