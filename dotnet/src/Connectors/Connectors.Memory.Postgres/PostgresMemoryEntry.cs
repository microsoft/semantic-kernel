// Copyright (c) Microsoft. All rights reserved.

using System;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.Memory.Postgres;

/// <summary>
/// A postgres memory entry.
/// </summary>
public record struct PostgresMemoryEntry
{
    /// <summary>
    /// Unique identifier of the memory entry.
    /// </summary>
    public string Key { get; set; }

    /// <summary>
    /// Metadata as a string.
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
