// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Represents a request to the <see cref="TextSearchStoreOptions.SourceRetrievalCallback"/>.
/// </summary>
[Experimental("SKEXP0130")]
public sealed class TextSearchStoreSourceRetrievalRequest
{
    /// <summary>
    /// Initializes a new instance of the <see cref="TextSearchStoreSourceRetrievalRequest"/> class.
    /// </summary>
    /// <param name="sourceId">The source ID of the document to retrieve.</param>
    /// <param name="sourceLink">The source link of the document to retrieve.</param>
    public TextSearchStoreSourceRetrievalRequest(string? sourceId, string? sourceLink)
    {
        this.SourceId = sourceId;
        this.SourceLink = sourceLink;
    }

    /// <summary>
    /// Gets or sets the source ID of the document to retrieve.
    /// </summary>
    public string? SourceId { get; set; }

    /// <summary>
    /// Gets or sets the source link of the document to retrieve.
    /// </summary>
    public string? SourceLink { get; set; }
}
