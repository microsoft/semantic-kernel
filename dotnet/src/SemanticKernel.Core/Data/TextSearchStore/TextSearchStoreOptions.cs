// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Contains options for the <see cref="TextSearchStore{TKey}"/>.
/// </summary>
[Experimental("SKEXP0130")]
public sealed class TextSearchStoreOptions
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
    /// Gets or sets a value indicating whether to use hybrid search if it is available for the provided vector store.
    /// </summary>
    /// <value>
    /// Defaults to <c>true</c> if not set.
    /// </value>
    public bool? UseHybridSearch { get; init; }

    /// <summary>
    /// Gets or sets a word segmenter function to split search text into separate words for the purposes of hybrid search.
    /// This will not be used if <see cref="UseHybridSearch"/> is set to <c>false</c>.
    /// </summary>
    /// <remarks>
    /// Defaults to a simple text-character-based segmenter that splits the text by any character that is not a text character.
    /// </remarks>
    public Func<string, ICollection<string>>? WordSegementer { get; init; }

    /// <summary>
    /// Gets or sets an optional callback to load the source text using the source id or source link
    /// if the source text is not persisted in the database.
    /// </summary>
    /// <remarks>
    /// The response should include the source id or source link, as provided in the request,
    /// plus the source text loaded from the source.
    /// </remarks>
    public Func<List<TextSearchStoreSourceRetrievalRequest>, Task<IEnumerable<TextSearchStoreSourceRetrievalResponse>>>? SourceRetrievalCallback { get; init; }
}
