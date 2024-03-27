// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Memory;
using Npgsql;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// Extension methods for adding <see cref="PostgresMemoryStore"/> to the IServiceCollection.
/// </summary>
public static class PostgresMemoryStoreExtensions
{
    /// <summary>
    /// Adds the <see cref="PostgresMemoryStore"/> implementation of <see cref="IMemoryStore"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The IServiceCollection to add the <see cref="PostgresMemoryStore"/> to.</param>
    /// <param name="serviceId">The optional service identifier.</param>
    /// <returns>The updated IServiceCollection.</returns>
    public static IServiceCollection AddPostgresMemoryStore(this IServiceCollection services, string? serviceId = null)
        => services.AddKeyedSingleton<IMemoryStore, PostgresMemoryStore>(serviceId);

    /// <summary>
    /// Adds the <see cref="PostgresMemoryStore"/> implementation of <see cref="IMemoryStore"/> to the <see cref="IServiceCollection"/> with the specified connection string, vector size, schema, and optional service identifier.
    /// </summary>
    /// <param name="services">The IServiceCollection to add the <see cref="PostgresMemoryStore"/> to.</param>
    /// <param name="connectionString">The connection string for the Postgres database.</param>
    /// <param name="vectorSize">The size of the vector.</param>
    /// <param name="schema">The schema name for the <see cref="PostgresMemoryStore"/>. Default value is PostgresMemoryStore.DefaultSchema.</param>
    /// <param name="serviceId">The optional service identifier.</param>
    /// <returns>The updated IServiceCollection.</returns>
    public static IServiceCollection AddPostgresMemoryStore(
        this IServiceCollection services,
        string connectionString,
        int vectorSize,
        string schema = PostgresMemoryStore.DefaultSchema,
        string? serviceId = null)
    {
        services.AddKeyedSingleton<NpgsqlDataSource>(serviceId, (_, _) =>
        {
            NpgsqlDataSourceBuilder dataSourceBuilder = new(connectionString);
            dataSourceBuilder.UseVector();
            return dataSourceBuilder.Build();
        });

        services.AddKeyedSingleton<IPostgresDbClient>(serviceId, (provider, _) =>
            new PostgresDbClient(provider.GetRequiredService<NpgsqlDataSource>(), schema, vectorSize));

        return services.AddPostgresMemoryStore(serviceId);
    }
}
