// Copyright (c) Microsoft. All rights reserved.

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
}
