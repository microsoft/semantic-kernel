// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

#pragma warning disable CA1054 // URI-like parameters should not be strings

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents audio content.
/// </summary>
[Experimental("SKEXP0001")]
public class DocContent : BinaryContent
{
    /// <summary>
    /// MIME Type of DOC (https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/MIME_types/Common_types)
    /// </summary>
    private const string DefaultMimeType = "application/msword";

    /// <summary>
    /// Initializes a new instance of the <see cref="DocContent"/> class.
    /// </summary>
    [JsonConstructor]
    public DocContent()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="DocContent"/> class.
    /// </summary>
    /// <param name="uri">The URI of the DOC file.</param>
    public DocContent(Uri uri) : base(uri)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="DocContent"/> class.
    /// </summary>
    /// <param name="dataUri">DataUri of the DOC</param>
    public DocContent(string dataUri) : base(dataUri)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="DocContent"/> class.
    /// </summary>
    /// <param name="data">Byte array of the DOC file</param>
    /// <param name="mimeType">Mime type of the DOC (defaults to standard for DOC)</param>
    public DocContent(ReadOnlyMemory<byte> data, string? mimeType = DefaultMimeType) : base(data, mimeType)
    {
    }
}
