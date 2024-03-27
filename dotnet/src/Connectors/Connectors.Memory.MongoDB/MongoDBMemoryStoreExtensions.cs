// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Memory;
using MongoDB.Driver;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;
/// <summary>
/// Extension methods for adding <see cref="MongoDBMemoryStore"/> to the IServiceCollection.
/// </summary>
public static class MongoDBMemoryStoreExtensions
{
    /// <summary>
    /// Adds <see cref="MongoDBMemoryStore"/> to the IServiceCollection.
    /// </summary>
    /// <param name="services">The IServiceCollection to add the MongoDBMemoryStore to.</param>
    /// <param name="databaseName">The name of the MongoDB database.</param>
    /// <param name="indexName">The name of the index.</param>
    /// <param name="serviceId">The optional service identifier.</param>
    /// <returns>The updated IServiceCollection.</returns>
    public static IServiceCollection AddMongoDBMemoryStore(
        this IServiceCollection services,
        string databaseName,
        string? indexName = default,
        string? serviceId = null) => services.AddKeyedSingleton<IMemoryStore>(serviceId, (provider, _) => new MongoDBMemoryStore(provider.GetRequiredService<IMongoClient>(), databaseName, indexName));

    /// <summary>
    /// Adds <see cref="MongoDBMemoryStore"/> to the IServiceCollection.
    /// </summary>
    /// <param name="services">The IServiceCollection to add the MongoDBMemoryStore to.</param>
    /// <param name="connectionString">The connection string for the MongoDB server.</param>
    /// <param name="databaseName">The name of the MongoDB database.</param>
    /// <param name="indexName">The name of the index.</param>
    /// <param name="serviceId">The optional service identifier.</param>
    /// <returns>The updated IServiceCollection.</returns>
    public static IServiceCollection AddMongoDBMemoryStore(
        this IServiceCollection services,
        string connectionString,
        string databaseName,
        string? indexName = default,
        string? serviceId = null)
    {
        services.AddKeyedSingleton<IMongoClient>(serviceId, new MongoClient(connectionString));
        return services.AddMongoDBMemoryStore(databaseName, indexName, serviceId);
    }
}
