// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// A postgres memory entry.
/// </summary>
[Experimental("SKEXP0020")]
public record struct PostgresMemoryEntry
{
    /// <summary>
    /// Unique identifier of the memory entry.
    /// </summary>
    public string Key { get; set; }

    /// <summary>
    /// Attributes as a string.
    /// </summary>
    public string MetadataString { get; set; }

    /// <summary>
    /// The embedding data as a <see cref="Vector"/>.
    /// </summary>
    public Vector? Embedding { get; set; }

    /// <summary>
    /// Optional timestamp. Its 'DateTimeKind' is <see cref="DateTimeKind.Utc"/>
    /// </summary>
    public DateTime? Timestamp { get; set; }
}
