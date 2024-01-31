---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: crickman, mabolan, semenshi
date: 2024-01-16
---

# File Services

## Context and Problem Statement
OpenAI provides a file service for uploading files to be used for *assistant retrieval* or *model fine-tuning*: `https://api.openai.com/v1/files`

Other providers may also offer some type of file-service, such as Gemini.

> Note: *Azure Open AI* does not currently support the OpenAI file service API.

## Considered Options

1. Add OpenAI file service support to `Microsoft.SemanticKernel.Experimental.Agents`
2. Add a file service abstraction and implement support for OpenAI
3. Add OpenAI file service support without abstraction

## Decision Outcome

> Option 2. **Add a file service abstraction and implement support for OpenAI**

Defining a generalized file service interface provides an extensibility point for other vendors, in addition to *OpenAI*.

## Pros and Cons of the Options

### Option 1. Add OpenAI file service support to `Microsoft.SemanticKernel.Experimental.Agents`
**Pro:**
1. No impact to existing AI connectors.

**Con:**
1. No reuse via AI connectors.
1. No common abstraction.
1. Unnatural dependency binding for uses other than with OpenAI assistants.

### Option 2. Add a file service abstraction and implement support for OpenAI
**Pro:**
1. Defines a common interface for file service interactions.
1. Allows for specialization for vendor specific services.

**Con:**
1. Other systems may diverge from existing assumptions.


### Option 3. Add OpenAI file service support without abstraction
**Pro:**
1. Provides support for OpenAI file-service.

**Con:**
1. File service offerings from other vendors supported case-by-case without commonality.


## More Information

Signatures for *Option 2*, but can adapt to any option.

#### `Microsoft.SemanticKernel.Abstractions`
```csharp
namespace Microsoft.SemanticKernel.Files;

public interface IFileService : IAIService
{
    Task<FileReference> GetFileAsync(
        string id,
        CancellationToken cancellationToken = default);

    Task<IEnumerable<FileReference>> GetFilesAsync(CancellationToken cancellationToken = default);

    Task<Stream> GetFileContentAsync(
        string id,
        CancellationToken cancellationToken = default);

    Task DeleteFileAsync(
        string id,
        CancellationToken cancellationToken = default);

    Task<FileReference> UploadContentAsync(
        IFileUploadRequest request,
        CancellationToken cancellationToken = default);
}


public interface IFileService<TFile, TRequest> : IFileService
    where TFile : FileReference
    where TRequest : IFileUploadRequest
{
    new Task<TFile> GetFileAsync(
        string id,
        CancellationToken cancellationToken = default);

    new Task<IEnumerable<TFile>> GetFilesAsync(
        CancellationToken cancellationToken = default);

    Task<TFile> UploadContentAsync(
        TRequest request,
        CancellationToken cancellationToken = default);
}

public interface IFileUploadRequest
{
    string FileName { get; }
 
    Stream GetContent();
}

public class FileReference
{
    public string Id { get; set; }

    public DateTime CreatedTimestamp { get; set; }

    public string FileName { get; set; }

    public int SizeInBytes { get; set; }
}
```

#### `Microsoft.SemanticKernel.Connectors.OpenAI`
```csharp
namespace Microsoft.SemanticKernel.Connectors.OpenAI;

public sealed class OpenAIFileService : IFileService<OpenAIFileReference, OpenAIFileUploadRequest>
{
    ...
}

public sealed class OpenAIFileUploadRequest : IFileUploadRequest
{
    public OpenAIFilePurpose Purpose { get; }

    ...
}

public sealed class OpenAIFileReference : FileReference
{
    public OpenAIFilePurpose Purpose { get; set; }
}

public enum OpenAIFilePurpose
{
    Assistants,
    Finetuning,
}
```