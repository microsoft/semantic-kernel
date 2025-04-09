// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

/// <summary>
/// A SQL Server or Azure SQL memory entry.
/// </summary>
[Experimental("SKEXP0020")]
internal record struct SqlServerMemoryEntry
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
    /// The embedding data.
    /// </summary>
    public ReadOnlyMemory<float>? Embedding { get; set; }

    /// <summary>
    /// Optional timestamp.
    /// </summary>
    public DateTimeOffset? Timestamp { get; set; }
}
