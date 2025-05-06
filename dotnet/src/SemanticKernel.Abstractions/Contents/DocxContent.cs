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
public class DocxContent : BinaryContent
{
    /// <summary>
    /// MIME Type of DOCX (https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/MIME_types/Common_types)
    /// </summary>
    private const string DefaultMimeType = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";

    /// <summary>
    /// Initializes a new instance of the <see cref="DocxContent"/> class.
    /// </summary>
    [JsonConstructor]
    public DocxContent()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="DocxContent"/> class.
    /// </summary>
    /// <param name="uri">The URI of the DOCX file.</param>
    public DocxContent(Uri uri) : base(uri)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="DocxContent"/> class.
    /// </summary>
    /// <param name="dataUri">DataUri of the DOCX</param>
    public DocxContent(string dataUri) : base(dataUri)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="DocxContent"/> class.
    /// </summary>
    /// <param name="data">Byte array of the DOCX file</param>
    /// <param name="mimeType">Mime type of the DOC (defaults to standard for DOCX)</param>
    public DocxContent(ReadOnlyMemory<byte> data, string? mimeType = DefaultMimeType) : base(data, mimeType)
    {
    }
}
