// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.Memory.Postgres;
using Npgsql;

#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides extension methods for the <see cref="KernelBuilder"/> class to configure Postgres connectors.
/// </summary>
public static class PostgresKernelBuilderExtensions
{
    /// <summary>
    /// Registers Postgres Memory Store.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="connectionString">Postgres database connection string.</param>
    /// <param name="vectorSize">Embedding vector size.</param>
    /// <param name="schema">Schema of collection tables.</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder WithPostgresMemoryStore(this KernelBuilder builder,
        string connectionString,
        int vectorSize,
        string schema = PostgresMemoryStore.DefaultSchema)
    {
        builder.WithMemoryStorage((loggerFactory) =>
        {
            return new PostgresMemoryStore(connectionString, vectorSize, schema);
        });

        return builder;
    }

    /// <summary>
    /// Registers Postgres Memory Store.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="dataSource">Postgres data source.</param>
    /// <param name="vectorSize">Embedding vector size.</param>
    /// <param name="schema">Schema of collection tables.</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder WithPostgresMemoryStore(this KernelBuilder builder,
        NpgsqlDataSource dataSource,
        int vectorSize,
        string schema = PostgresMemoryStore.DefaultSchema)
    {
        builder.WithMemoryStorage((loggerFactory) =>
        {
            return new PostgresMemoryStore(dataSource, vectorSize, schema);
        });

        return builder;
    }

    /// <summary>
    /// Registers Postgres Memory Store.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="postgresDbClient">Postgres database client.</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder WithPostgresMemoryStore(this KernelBuilder builder, IPostgresDbClient postgresDbClient)
    {
        builder.WithMemoryStorage((loggerFactory) =>
        {
            return new PostgresMemoryStore(postgresDbClient);
        });

        return builder;
    }
}
