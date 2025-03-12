// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

/// <summary>
/// Options for creating a <see cref="SqlServerVectorStore"/>.
/// </summary>
public sealed class SqlServerVectorStoreOptions
{
    internal static readonly SqlServerVectorStoreOptions Defaults = new();

    /// <summary>
    /// Gets or sets the database schema.
    /// </summary>
    public string? Schema { get; init; } = null;
}
