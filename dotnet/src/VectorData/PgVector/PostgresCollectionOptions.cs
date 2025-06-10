// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

/// <summary>
/// Options when creating a <see cref="PostgresCollection{TKey, TRecord}"/>.
/// </summary>
public sealed class PostgresCollectionOptions : VectorStoreCollectionOptions
{
    internal static readonly PostgresCollectionOptions Default = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresCollectionOptions"/> class.
    /// </summary>
    public PostgresCollectionOptions()
    {
    }

    internal PostgresCollectionOptions(PostgresCollectionOptions? source) : base(source)
    {
        this.Schema = source?.Schema ?? PostgresVectorStoreOptions.Default.Schema;
    }

    /// <summary>
    /// Gets or sets the database schema.
    /// </summary>
    public string Schema { get; set; } = PostgresVectorStoreOptions.Default.Schema;
}
