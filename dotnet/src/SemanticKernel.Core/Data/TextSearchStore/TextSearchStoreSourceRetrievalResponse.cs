// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Represents a response from the <see cref="TextSearchStoreOptions.SourceRetrievalCallback"/>.
/// </summary>
[Experimental("SKEXP0130")]
public sealed class TextSearchStoreSourceRetrievalResponse
{
    /// <summary>
    /// Initializes a new instance of the <see cref="TextSearchStoreSourceRetrievalResponse"/> class.
    /// </summary>
    /// <param name="request">The request matching this response.</param>
    /// <param name="text">The source text that was retrieved.</param>
    public TextSearchStoreSourceRetrievalResponse(TextSearchStoreSourceRetrievalRequest request, string text)
    {
        Verify.NotNull(request);
        Verify.NotNull(text);

        this.SourceId = request.SourceId;
        this.SourceLink = request.SourceLink;
        this.Text = text;
    }

    /// <summary>
    /// Gets or sets the source ID of the document that was retrieved.
    /// </summary>
    public string? SourceId { get; set; }

    /// <summary>
    /// Gets or sets the source link of the document that was retrieved.
    /// </summary>
    public string? SourceLink { get; set; }

    /// <summary>
    /// Gets or sets the source text of the document that was retrieved.
    /// </summary>
    public string Text { get; set; }
}
