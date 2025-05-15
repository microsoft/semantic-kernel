// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Npgsql;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

/// <summary>
/// Represents a collection of vector store records in a Postgres database, mapped to a dynamic <c>Dictionary&lt;string, object?&gt;</c>.
/// </summary>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class PostgresDynamicCollection : PostgresCollection<object, Dictionary<string, object?>>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresDynamicCollection"/> class.
    /// </summary>
    /// <param name="dataSource">The data source to use for connecting to the database.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="ownsDataSource">A value indicating whether the data source should be disposed when the collection is disposed.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public PostgresDynamicCollection(NpgsqlDataSource dataSource, string name, bool ownsDataSource, PostgresCollectionOptions options)
        : this(() => new PostgresDbClient(dataSource, options?.Schema, ownsDataSource), name, options)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="connectionString">Postgres database connection string.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public PostgresDynamicCollection(string connectionString, string name, PostgresCollectionOptions options)
        : this(() => new PostgresDbClient(PostgresUtils.CreateDataSource(connectionString), options?.Schema, ownsDataSource: true), name, options)
    {
    }

    internal PostgresDynamicCollection(Func<PostgresDbClient> clientFactory, string name, PostgresCollectionOptions options)
        : base(
            clientFactory,
            name,
            static options => new PostgresModelBuilder().BuildDynamic(
                options.Definition ?? throw new ArgumentException("Definition is required for dynamic collections"),
                options.EmbeddingGenerator),
            options)
    {
    }
}
