// Copyright (c) Microsoft. All rights reserved.
#pragma warning disable IDE0005 // Using directive is unnecessary
using System.Collections.Concurrent;
using System.ComponentModel;
using System.Text.Json;
using Microsoft.Azure.Cosmos;
using Microsoft.SemanticKernel;
using Newtonsoft.Json;
#pragma warning restore IDE0005 // Using directive is unnecessary

namespace ProcessWithCloudEvents.SharedComponents.Storage;

// CosmosDB V3 has a dependency on Newtonsoft.Json, so need to add wrapper class for Cosmos DB entities:
// https://brettmckenzie.net/posts/the-input-content-is-invalid-because-the-required-properties-id-are-missing/
public record CosmosDbEntity<T>
{
    [JsonProperty("id")]
    public string Id { get; init; }

    [JsonProperty("body")]
    public T Body { get; init; }

    [JsonProperty("instanceId")]
    public string PartitionKey { get; init; }
}

internal sealed class CosmosDbProcessStorageConnector : IProcessStorageConnector
{
    private readonly CosmosClient _cosmosClient;
    private readonly Microsoft.Azure.Cosmos.Container _container;
    private readonly string _databaseId;
    private readonly string _containerId;

    public CosmosDbProcessStorageConnector(string connectionString, string databaseId, string containerId)
    {
        this._cosmosClient = new CosmosClient(connectionString);
        this._databaseId = databaseId;
        this._containerId = containerId;
        this._container = this._cosmosClient.GetContainer(databaseId, containerId);
    }

    public async ValueTask OpenConnectionAsync()
    {
        // Cosmos DB client handles connection pooling internally, so just ensure the client is initialized  
        await Task.CompletedTask;
    }

    public async ValueTask CloseConnectionAsync()
    {
        // Dispose the CosmosClient to close connections  
        this._cosmosClient.Dispose();
        await Task.CompletedTask;
    }

    public async Task<TEntry?> GetEntryAsync<TEntry>(string id) where TEntry : class
    {
        try
        {
            var response = await this._container.ReadItemAsync<CosmosDbEntity<TEntry>>(id, new PartitionKey(id));
            return response.Resource.Body;
        }
        catch (CosmosException ex) when (ex.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            // Item not found  
            return null;
        }
    }

    public async Task<bool> SaveEntryAsync<TEntry>(string id, string type, TEntry entry) where TEntry : class
    {
        try
        {
            var wrappedEntry = new CosmosDbEntity<TEntry>
            {
                Id = id,
                Body = entry,
                PartitionKey = id
            };
            await this._container.UpsertItemAsync(wrappedEntry, new PartitionKey(id));
            return true;
        }
        catch (CosmosException ex)
        {
            // Handle exceptions as needed, log them, etc.  
            Console.WriteLine($"Error saving entry: {ex.Message}");
            return false;
        }
    }

    public async Task<bool> DeleteEntryAsync(string id)
    {
        try
        {
            await this._container.DeleteItemAsync<object>(id, new PartitionKey(id));
            return true;
        }
        catch (CosmosException ex) when (ex.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            // Item not found  
            return false;
        }
    }
}
