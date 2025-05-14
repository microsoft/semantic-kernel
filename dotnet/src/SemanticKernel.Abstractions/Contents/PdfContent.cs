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
public class PdfContent : BinaryContent
{
    /// <summary>
    /// MIME Type of PDF (https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/MIME_types/Common_types)
    /// </summary>
    private const string DefaultMimeType = "application/pdf";

    /// <summary>
    /// Initializes a new instance of the <see cref="PdfContent"/> class.
    /// </summary>
    [JsonConstructor]
    public PdfContent()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PdfContent"/> class.
    /// </summary>
    /// <param name="uri">The URI of PDF file.</param>
    public PdfContent(Uri uri) : base(uri)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PdfContent"/> class.
    /// </summary>
    /// <param name="dataUri">DataUri of the PDF</param>
    public PdfContent(string dataUri) : base(dataUri)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PdfContent"/> class.
    /// </summary>
    /// <param name="data">Byte array of the PDF file</param>
    /// <param name="mimeType">Mime type of the PDF (defaults to standard for PDF)</param>
    public PdfContent(ReadOnlyMemory<byte> data, string? mimeType = DefaultMimeType) : base(data, mimeType)
    {
    }
}
