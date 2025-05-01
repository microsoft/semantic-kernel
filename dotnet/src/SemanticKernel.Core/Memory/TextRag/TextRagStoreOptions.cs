// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Contains options for the <see cref="TextRagStore{TKey}"/>.
/// </summary>
public sealed class TextRagStoreOptions
{
    /// <summary>
    /// Gets or sets an optional namespace to pre-filter the possible
    /// records with when doing a vector search.
    /// </summary>
    public string? SearchNamespace { get; init; }

    /// <summary>
    /// Gets or sets a value indicating whether to use the source ID as the primary key for records.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Using the source ID as the primary key allows for easy updates from the source for any changed
    /// records, since those records can just be upserted again, and will overwrite the previous version
    /// of the same record.
    /// </para>
    /// <para>
    /// This setting can only be used when the chosen key type is a string.
    /// </para>
    /// </remarks>
    /// <value>
    /// Defaults to <c>false</c> if not set.
    /// </value>
    public bool? UseSourceIdAsPrimaryKey { get; init; }

    /// <summary>
    /// Gets or sets an optional callback to load the source text from the source id or source link
    /// if the source text is not persisted in the database.
    /// </summary>
    public SourceRetriever? SourceRetrievalCallback { get; init; }

    /// <summary>
    /// Delegate type for loading the source text from the source id or source link
    /// if the source text is not persisted in the database.
    /// </summary>
    /// <param name="sourceIds">The ids and links of the text to load.</param>
    /// <returns>The source text with the source id or source link.</returns>
    public delegate Task<IEnumerable<(string? sourceId, string? sourceLink, string text)>> SourceRetriever(List<(string? sourceId, string? sourceLink)> sourceIds);
}
