// Copyright (c) Microsoft. All rights reserved.

using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.Memory.Postgres;

/// <summary>
/// A postgres memory entry.
/// </summary>
internal struct DatabaseEntry
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
    /// Optional timestamp.
    /// </summary>
    public long? Timestamp { get; set; }
}
