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
    public string Schema { get; init; } = "dbo";

    /// <summary>
    /// Number of dimensions that stored embeddings will use.
    /// </summary>
    // TODO: adsitnik: this design most likely won't need this setting,
    // as it up to the TRecrod to define the dimensions.
    public int EmbeddingDimensionsCount { get; init; } = 1536;
}
