---
contact: crickman, mabolan, semenshi
date: 2024-01-16T00:00:00Z
runme:
  document:
    relativePath: 0026-file-service.md
  session:
    id: 01J6M121KZGM9SEYRDY5S4XM4B
    updated: 2024-08-31 11:00:10Z
status: proposed
---

# File Services

## Context and Problem Statement

OpenAI provides a file service for uploading files to be used for *assistant retrieval* or *model fine-tuning*: `ht***************************es`

Other providers may also offer some type of file-service, such as Gemini.

> Note: *Azure Open AI* does not currently support the OpenAI file service API.

## Considered Options

1. Add OpenAI file service support to `Microsoft.SemanticKernel.Experimental.Agents`
2. Add a file service abstraction and implement support for OpenAI
3. Add OpenAI file service support without abstraction

## Decision Outcome

> Option 3. **Add OpenAI file service support without abstraction**
> Mark code as experimental using label: `SK*****10`

Defining a generalized file service interface provides an extensibility point for other vendors, in addition to *OpenAI*.

## Pros and Cons of the Options

### Option 1. Add OpenAI file service support to `Microsoft.SemanticKernel.Experimental.Agents`

**Pro:**

1. No impact to existing AI connectors.

**Con:**

1. No reuse via AI connectors.
2. No common abstraction.
3. Unnatural dependency binding for uses other than with OpenAI assistants.

### Option 2. Add a file service abstraction and implement support for OpenAI

**Pro:**

1. Defines a common interface for file service interactions.
2. Allows for specialization for vendor specific services.

**Con:**

1. Other systems may diverge from existing assumptions.

### Option 3. Add OpenAI file service support without abstraction

**Pro:**

1. Provides support for OpenAI file-service.

**Con:**

1. File service offerings from other vendors supported case-by-case without commonality.

## More Information

### Signature of BinaryContent

> Note: `BinaryContent` object able to provide either `BinaryData` or `Stream` regardless of which constructor is invoked.

 `Microsoft.SemanticKernel.Abstractions`

```csharp {"id":"01J6KQ3GKCRWDCGE797WGPR3BC"}
namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents binary content.
/// </summary>
public sealed class BinaryContent : KernelContent
{
    public BinaryContent(
        BinaryData content,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null);

    public BinaryContent(
        Func<Stream> streamProvider,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null);

    public Task<BinaryData> GetContentAsync();

    public Task<Stream> GetStreamAsync();
}
```

### Signatures for Option 3:

 `Microsoft.SemanticKernel.Connectors.OpenAI`

```csharp {"id":"01J6KQ3GKCRWDCGE797X9Q2N96"}
namespace Microsoft.SemanticKernel.Connectors.OpenAI;

public sealed class OpenAIFileService
{
    public async Task<OpenAIFileReference> GetFileAsync(
        string id,
        CancellationToken cancellationToken = default);

    public async Task<IEnumerable<OpenAIFileReference>> GetFilesAsync(CancellationToken cancellationToken = default);

    public async Task<BinaryContent> GetFileContentAsync(
        string id,
        CancellationToken cancellationToken = default);

    public async Task DeleteFileAsync(
        string id,
        CancellationToken cancellationToken = default);

    public async Task<OpenAIFileReference> UploadContentAsync(
        BinaryContent content,
        OpenAIFileUploadExecutionSettings settings,
        CancellationToken cancellationToken = default);
}

public sealed class OpenAIFileUploadExecutionSettings
{
    public string FileName { get; }
 
    public OpenAIFilePurpose Purpose { get; }
}

public sealed class OpenAIFileReference
{
    public string Id { get; set; }

    public DateTime CreatedTimestamp { get; set; }

    public string FileName { get; set; }
    
    public OpenAIFilePurpose Purpose { get; set; }

    public int SizeInBytes { get; set; }
}

public enum OpenAIFilePurpose
{
    Assistants,
    Finetuning,
}
```
