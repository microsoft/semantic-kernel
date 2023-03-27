// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Copy of metadata associated with a memory entry.
/// </summary>
public class MemoryQueryResult
{
    /// <summary>
    /// Whether the source data used to calculate embeddings are stored in the local
    /// storage provider or is available through and external service, such as web site, MS Graph, etc.
    /// </summary>
    public bool IsReference { get; }

    /// <summary>
    /// A value used to understand which external service owns the data, to avoid storing the information
    /// inside the URI. E.g. this could be "MSTeams", "WebSite", "GitHub", etc.
    /// </summary>
    public string ExternalSourceName { get; }

    /// <summary>
    /// Unique identifier. The format of the value is domain specific, so it can be a URL, a GUID, etc.
    /// </summary>
    public string Id { get; }

    /// <summary>
    /// Optional entry description, useful for external references when Text is empty.
    /// </summary>
    public string Description { get; }

    /// <summary>
    /// Source text, available only when the memory is not an external source.
    /// </summary>
    public string Text { get; }

    /// <summary>
    /// Search relevance, from 0 to 1, where 1 means perfect match.
    /// </summary>
    public double Relevance { get; }

    /// <summary>
    /// Create new instance
    /// </summary>
    /// <param name="isReference">Whether the source data used to calculate embeddings are stored in the local
    /// storage provider or is available through and external service, such as web site, MS Graph, etc.</param>
    /// <param name="sourceName">A value used to understand which external service owns the data, to avoid storing the information
    /// inside the Id. E.g. this could be "MSTeams", "WebSite", "GitHub", etc.</param>
    /// <param name="id">Unique identifier. The format of the value is domain specific, so it can be a URL, a GUID, etc.</param>
    /// <param name="description">Optional title describing the entry, useful for external references when Text is empty.</param>
    /// <param name="text">Source text, available only when the memory is not an external source.</param>
    /// <param name="relevance">Search relevance, from 0 to 1, where 1 means perfect match.</param>
    public MemoryQueryResult(
        bool isReference,
        string sourceName,
        string id,
        string description,
        string text,
        double relevance)
    {
        this.IsReference = isReference;
        this.ExternalSourceName = sourceName;
        this.Id = id;
        this.Description = description;
        this.Text = text;
        this.Relevance = relevance;
    }

    internal static MemoryQueryResult FromMemoryRecord(
        MemoryRecord rec,
        double relevance)
    {
        return new MemoryQueryResult(
            isReference: rec.Metadata.IsReference,
            sourceName: rec.Metadata.ExternalSourceName,
            id: rec.Metadata.Id,
            description: rec.Metadata.Description,
            text: rec.Metadata.Text,
            relevance);
    }
}
