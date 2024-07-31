// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Grpc.Core;
using Microsoft.SemanticKernel.Data;
using Pinecone.Grpc;
using Sdk = Pinecone;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Service for storing and retrieving vector records, that uses Pinecone as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class PineconeVectorStoreRecordCollection<TRecord> : IVectorStoreRecordCollection<string, TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
    where TRecord : class
{
    private const string DatabaseName = "Pinecone";
    private const string CreateCollectionName = "CreateCollection";
    private const string CollectionExistsName = "CollectionExists";
    private const string DeleteCollectionName = "DeleteCollection";

    private const string UpsertOperationName = "Upsert";
    private const string DeleteOperationName = "Delete";
    private const string GetOperationName = "Get";

    private readonly Sdk.PineconeClient _pineconeClient;
    private readonly PineconeVectorStoreRecordCollectionOptions<TRecord> _options;
    private readonly VectorStoreRecordDefinition _vectorStoreRecordDefinition;
    private readonly IVectorStoreRecordMapper<TRecord, Sdk.Vector> _mapper;

    private Sdk.Index<GrpcTransport>? _index;

    /// <inheritdoc />
    public string CollectionName { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="PineconeVectorStoreRecordCollection{TRecord}"/> class.
    /// </summary>
    /// <param name="pineconeClient">Pinecone client that can be used to manage the collections and vectors in a Pinecone store.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <exception cref="ArgumentNullException">Thrown if the <paramref name="pineconeClient"/> is null.</exception>
    /// <param name="collectionName">The name of the collection that this <see cref="PineconeVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <exception cref="ArgumentException">Thrown for any misconfigured options.</exception>
    public PineconeVectorStoreRecordCollection(Sdk.PineconeClient pineconeClient, string collectionName, PineconeVectorStoreRecordCollectionOptions<TRecord>? options = null)
    {
        Verify.NotNull(pineconeClient);

        this._pineconeClient = pineconeClient;
        this.CollectionName = collectionName;
        this._options = options ?? new PineconeVectorStoreRecordCollectionOptions<TRecord>();
        this._vectorStoreRecordDefinition = this._options.VectorStoreRecordDefinition ?? VectorStoreRecordPropertyReader.CreateVectorStoreRecordDefinitionFromType(typeof(TRecord), true);

        if (this._options.VectorCustomMapper is null)
        {
            this._mapper = new PineconeVectorStoreRecordMapper<TRecord>(this._vectorStoreRecordDefinition);
        }
        else
        {
            this._mapper = this._options.VectorCustomMapper;
        }
    }

    /// <inheritdoc />
    public async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        var result = await this.RunOperationAsync(
            CollectionExistsName,
            async () =>
            {
                var collections = await this._pineconeClient.ListIndexes(cancellationToken).ConfigureAwait(false);

                return collections.Any(x => x.Name == this.CollectionName);
            }).ConfigureAwait(false);

        return result;
    }

    /// <inheritdoc />
    public async Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        // we already run through record property validation, so a single VectorStoreRecordVectorProperty is guaranteed.
        var vectorProperty = this._vectorStoreRecordDefinition.Properties.OfType<VectorStoreRecordVectorProperty>().First();
        var (dimension, metric) = PineconeVectorStoreCollectionCreateMapping.MapServerlessIndex(vectorProperty);

        await this.RunOperationAsync(
            CreateCollectionName,
            () => this._pineconeClient.CreateServerlessIndex(
                this.CollectionName,
                dimension,
                metric,
                this._options.ServerlessIndexCloud,
                this._options.ServerlessIndexRegion,
                cancellationToken)).ConfigureAwait(false);
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
    public Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
        => this.RunOperationAsync(
            DeleteCollectionName,
            () => this._pineconeClient.DeleteIndex(this.CollectionName, cancellationToken));

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(string key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        var records = await this.GetBatchAsync([key], options, cancellationToken).ToListAsync(cancellationToken).ConfigureAwait(false);

        return records.FirstOrDefault();
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetBatchAsync(
        IEnumerable<string> keys,
        GetRecordOptions? options = default,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        var indexNamespace = this.GetIndexNamespace();
        var mapperOptions = new StorageToDataModelMapperOptions { IncludeVectors = options?.IncludeVectors ?? false };

        var index = await this.GetIndexAsync(this.CollectionName, cancellationToken).ConfigureAwait(false);

        var results = await this.RunOperationAsync(
            GetOperationName,
            () => index.Fetch(keys, indexNamespace, cancellationToken)).ConfigureAwait(false);

        var records = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this.CollectionName,
            GetOperationName,
            () => results.Values.Select(x => this._mapper.MapFromStorageToDataModel(x, mapperOptions)).ToList());

        foreach (var record in records)
        {
            yield return record;
        }
    }

    /// <inheritdoc />
    public Task DeleteAsync(string key, DeleteRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(key);

        return this.DeleteBatchAsync([key], options, cancellationToken);
    }

    /// <inheritdoc />
    public async Task DeleteBatchAsync(IEnumerable<string> keys, DeleteRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        var indexNamespace = this.GetIndexNamespace();

        var index = await this.GetIndexAsync(this.CollectionName, cancellationToken).ConfigureAwait(false);

        await this.RunOperationAsync(
            DeleteOperationName,
            () => index.Delete(keys, indexNamespace, cancellationToken)).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task<string> UpsertAsync(TRecord record, UpsertRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        var indexNamespace = this.GetIndexNamespace();

        var index = await this.GetIndexAsync(this.CollectionName, cancellationToken).ConfigureAwait(false);

        var vector = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this.CollectionName,
            UpsertOperationName,
            () => this._mapper.MapFromDataToStorageModel(record));

        await this.RunOperationAsync(
            UpsertOperationName,
            () => index.Upsert([vector], indexNamespace, cancellationToken)).ConfigureAwait(false);

        return vector.Id;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> UpsertBatchAsync(
        IEnumerable<TRecord> records,
        UpsertRecordOptions? options = default,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        var indexNamespace = this.GetIndexNamespace();

        var index = await this.GetIndexAsync(this.CollectionName, cancellationToken).ConfigureAwait(false);

        var vectors = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this.CollectionName,
            UpsertOperationName,
            () => records.Select(this._mapper.MapFromDataToStorageModel).ToList());

        await this.RunOperationAsync(
            UpsertOperationName,
            () => index.Upsert(vectors, indexNamespace, cancellationToken)).ConfigureAwait(false);

        foreach (var vector in vectors)
        {
            yield return vector.Id;
        }
    }

    private async Task<T> RunOperationAsync<T>(string operationName, Func<Task<T>> operation)
    {
        try
        {
            return await operation.Invoke().ConfigureAwait(false);
        }
        catch (RpcException ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreType = DatabaseName,
                CollectionName = this.CollectionName,
                OperationName = operationName
            };
        }
    }

    private async Task RunOperationAsync(string operationName, Func<Task> operation)
    {
        try
        {
            await operation.Invoke().ConfigureAwait(false);
        }
        catch (RpcException ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreType = DatabaseName,
                CollectionName = this.CollectionName,
                OperationName = operationName
            };
        }
    }

    private async Task<Sdk.Index<GrpcTransport>> GetIndexAsync(string indexName, CancellationToken cancellationToken)
    {
        this._index ??= await this._pineconeClient.GetIndex(indexName, cancellationToken).ConfigureAwait(false);

        return this._index;
    }

    private string? GetIndexNamespace()
        => this._options.IndexNamespace;
}
