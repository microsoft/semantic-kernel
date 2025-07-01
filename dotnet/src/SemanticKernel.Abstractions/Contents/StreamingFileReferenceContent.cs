// Copyright (c) Microsoft. All rights reserved.
using System.Diagnostics.CodeAnalysis;
using System.Text;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Content type to support file references.
/// </summary>
[Experimental("SKEXP0110")]
public class StreamingFileReferenceContent : StreamingKernelContent
{
    /// <summary>
    /// The file identifier.
    /// </summary>
    public string FileId { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="StreamingFileReferenceContent"/> class.
    /// </summary>
    /// <param name="fileId">The identifier of the referenced file.</param>
    [JsonConstructor]
    public StreamingFileReferenceContent(string fileId)
    {
        Verify.NotNullOrWhiteSpace(fileId, nameof(fileId));

        this.FileId = fileId;
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.FileId;
    }

    /// <inheritdoc/>
    public override byte[] ToByteArray()
    {
        return Encoding.UTF8.GetBytes(this.ToString());
    }
}
