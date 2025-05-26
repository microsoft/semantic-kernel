// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Represents a document that can be used for Retrieval Augmented Generation (RAG).
/// </summary>
[Experimental("SKEXP0130")]
public sealed class TextSearchDocument
{
    /// <summary>
    /// Gets or sets an optional list of namespaces that the document should belong to.
    /// </summary>
    /// <remarks>
    /// A namespace is a logical grouping of documents, e.g. may include a group id to scope the document to a specific group of users.
    /// </remarks>
    public IList<string> Namespaces { get; set; } = [];

    /// <summary>
    /// Gets or sets the content as text.
    /// </summary>
    public string? Text { get; set; }

    /// <summary>
    /// Gets or sets an optional source ID for the document.
    /// </summary>
    /// <remarks>
    /// This ID should be unique within the collection that the document is stored in, and can
    /// be used to map back to the source artifact for this document.
    /// If updates need to be made later or the source document was deleted and this document
    /// also needs to be deleted, this id can be used to find the document again.
    /// </remarks>
    public string? SourceId { get; set; }

    /// <summary>
    /// Gets or sets an optional name for the source document.
    /// </summary>
    /// <remarks>
    /// This can be used to provide display names for citation links when the document is referenced as
    /// part of a response to a query.
    /// </remarks>
    public string? SourceName { get; set; }

    /// <summary>
    /// Gets or sets an optional link back to the source of the document.
    /// </summary>
    /// <remarks>
    /// This can be used to provide citation links when the document is referenced as
    /// part of a response to a query.
    /// </remarks>
    public string? SourceLink { get; set; }
}
