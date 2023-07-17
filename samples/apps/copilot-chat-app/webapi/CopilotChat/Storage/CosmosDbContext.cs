// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;

namespace SemanticKernel.Service.CopilotChat.Storage;

/// <summary>
/// A storage context that stores entities in a CosmosDB container.
/// </summary>
public class CosmosDbContext<T> : IStorageContext<T>, IDisposable where T : IStorageEntity
{
    /// <summary>
    /// The CosmosDB client.
    /// </summary>
    private readonly CosmosClient _client;

    /// <summary>
    /// CosmosDB container.
    /// </summary>
    private readonly Container _container;

    /// <summary>
    /// Initializes a new instance of the CosmosDbContext class.
    /// </summary>
    /// <param name="connectionString">The CosmosDB connection string.</param>
    /// <param name="database">The CosmosDB database name.</param>
    /// <param name="container">The CosmosDB container name.</param>
    public CosmosDbContext(string connectionString, string database, string container)
    {
        // Configure JsonSerializerOptions
        var options = new CosmosClientOptions
        {
            SerializerOptions = new CosmosSerializationOptions
            {
                PropertyNamingPolicy = CosmosPropertyNamingPolicy.CamelCase
            },
        };
        this._client = new CosmosClient(connectionString, options);
        this._container = this._client.GetContainer(database, container);
    }

    /// <inheritdoc/>
    public async Task<IEnumerable<T>> QueryEntitiesAsync(Func<T, bool> predicate)
    {
        return await Task.Run<IEnumerable<T>>(
            () => this._container.GetItemLinqQueryable<T>(true).Where(predicate).AsEnumerable());
    }

    /// <inheritdoc/>
    public async Task CreateAsync(T entity)
    {
        if (string.IsNullOrWhiteSpace(entity.Id))
        {
            throw new ArgumentOutOfRangeException(nameof(entity.Id), "Entity Id cannot be null or empty.");
        }

        await this._container.CreateItemAsync(entity);
    }

    /// <inheritdoc/>
    public async Task DeleteAsync(T entity)
    {
        if (string.IsNullOrWhiteSpace(entity.Id))
        {
            throw new ArgumentOutOfRangeException(nameof(entity.Id), "Entity Id cannot be null or empty.");
        }

        await this._container.DeleteItemAsync<T>(entity.Id, new PartitionKey(entity.Id));
    }

    /// <inheritdoc/>
    public async Task<T> ReadAsync(string entityId)
    {
        if (string.IsNullOrWhiteSpace(entityId))
        {
            throw new ArgumentOutOfRangeException(nameof(entityId), "Entity Id cannot be null or empty.");
        }

        try
        {
            var response = await this._container.ReadItemAsync<T>(entityId, new PartitionKey(entityId));
            return response.Resource;
        }
        catch (CosmosException ex) when (ex.StatusCode == HttpStatusCode.NotFound)
        {
            throw new KeyNotFoundException($"Entity with id {entityId} not found.");
        }
    }

    /// <inheritdoc/>
    public async Task UpsertAsync(T entity)
    {
        if (string.IsNullOrWhiteSpace(entity.Id))
        {
            throw new ArgumentOutOfRangeException(nameof(entity.Id), "Entity Id cannot be null or empty.");
        }

        await this._container.UpsertItemAsync(entity);
    }

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._client.Dispose();
        }
    }
}
