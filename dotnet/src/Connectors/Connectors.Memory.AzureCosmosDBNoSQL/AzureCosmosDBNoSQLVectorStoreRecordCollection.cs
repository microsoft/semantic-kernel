// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

/// <summary>
/// Service for storing and retrieving vector records, that uses Azure CosmosDB NoSQL as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class AzureCosmosDBNoSQLVectorStoreRecordCollection<TRecord> : IVectorStoreRecordCollection<string, TRecord> where TRecord : class
#pragma warning restore CA1711 // Identifiers should not have incorrect
{
    /// <summary>The name of this database for telemetry purposes.</summary>
    private const string DatabaseName = "AzureCosmosDBNoSQL";

    /// <summary><see cref="Database"/> that can be used to manage the collections in Azure CosmosDB NoSQL.</summary>
    private readonly Database _database;

    /// <summary><see cref="Container"/> that can be used to manage the collections in Azure CosmosDB NoSQL.</summary>
    private readonly Container _container;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly AzureCosmosDBNoSQLVectorStoreRecordCollectionOptions<TRecord> _options;

    /// <inheritdoc />
    public string CollectionName { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureCosmosDBNoSQLVectorStoreRecordCollection{TRecord}"/> class.
    /// </summary>
    /// <param name="database"><see cref="Database"/> that can be used to manage the collections in Azure CosmosDB NoSQL.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="AzureCosmosDBNoSQLVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public AzureCosmosDBNoSQLVectorStoreRecordCollection(
        Database database,
        string collectionName,
        AzureCosmosDBNoSQLVectorStoreRecordCollectionOptions<TRecord>? options = default)
    {
        Verify.NotNull(database);
        Verify.NotNullOrWhiteSpace(collectionName);

        this._database = database;
        this.CollectionName = collectionName;
        this._container = this._database.GetContainer(this.CollectionName);
        this._options = options ?? new();
    }

    /// <inheritdoc />
    public async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        return await this.RunOperationAsync("CollectionExists", async () =>
        {
            const string Query = "SELECT VALUE(c.id) FROM c WHERE c.id = @collectionName";

            var queryDefinition = new QueryDefinition(Query).WithParameter("@collectionName", this.CollectionName);

            using var feedIterator = this._database.GetContainerQueryIterator<string>(queryDefinition);

            while (feedIterator.HasMoreResults)
            {
                var next = await feedIterator.ReadNextAsync(cancellationToken).ConfigureAwait(false);

                foreach (var containerName in next.Resource)
                {
                    return true;
                }
            }

            return false;
        }).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    /// <inheritdoc />
    public async Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        if (!await this.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
        {
            await this.CreateCollectionAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public Task DeleteAsync(string key, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    /// <inheritdoc />
    public Task DeleteBatchAsync(IEnumerable<string> keys, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    /// <inheritdoc />
    public async Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        await this._container
            .DeleteContainerAsync(cancellationToken: cancellationToken)
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public Task<TRecord?> GetAsync(string key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    /// <inheritdoc />
    public IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<string> keys, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    /// <inheritdoc />
    public Task<string> UpsertAsync(TRecord record, UpsertRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    /// <inheritdoc />
    public IAsyncEnumerable<string> UpsertBatchAsync(IEnumerable<TRecord> records, UpsertRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    #region

    private async Task<T> RunOperationAsync<T>(string operationName, Func<Task<T>> operation)
    {
        try
        {
            return await operation.Invoke().ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreType = DatabaseName,
                CollectionName = this.CollectionName,
                OperationName = operationName
            };
        }
    }

    #endregion
}
