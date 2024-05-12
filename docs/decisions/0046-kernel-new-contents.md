---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: rogerbarreto
date: 2024-05-02
deciders: rogerbarreto, markwallace-microsoft, sergeymenkshi, dmytrostruk, sergeymenshik, westey-m, matthewbolanos
---

# New Kernel Content Abstractions

## Context and Problem Statement

Currently, we don't have abstractions for some specific content types that are common in AI scenarios, such as

- FileContent
- [ClassificationContent](https://github.com/microsoft/semantic-kernel/pull/5279/files?short_path=1c2ab20#diff-1c2ab20229a57e9265f2a22490fe7543d3c58710c6eb75d04606ee394ab3cfd0) WIP ADR
- VideoResult
- JsonResult
- Audio Streaming

### File Content

`FileContent` can be provided as a `BinaryContent` decorator for any content that can be available as a File.

Major points:

- Files not necessarily need to be a retrivable, can be just be a indication or a reference to a file.
- Files are always pointers to binary contents, but not all Binary Contents will be used as files.
- Not all images/audios/videos will be files, but all of them are binary contents.

Class Scenarios:

File

```csharp
class FileContent : KernelContent {
    public string FileName { get; set; }
    public BinaryContent Content { get; set; }

    public string MimeType => Content.MimeType;
    ctor(KernelContent content, string fileName, ...) : base(...)
}
```

- ImageContent -> BinaryContent -> KernelContent
- FileContent -> KernelContent
- FileContent(ImageContent) -> KernelContent

```csharp
public sealed class FileContent : KernelContent
{
    // More file specific properties ...
    public string FileName { get; set; }

    // Reference to the binary content
    public MimeType => Content.MimeType;
    public Metadata => Content.Metadata;

    // Retrievable binary file content
    public BinaryContent Content { get; set; }

    ctor(KernelContent content, string fileName, string mimeType)
}

```

TBD
