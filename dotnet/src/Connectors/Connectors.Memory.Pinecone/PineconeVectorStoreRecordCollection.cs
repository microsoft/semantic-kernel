// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Grpc.Core;
using Microsoft.Extensions.VectorData;
using Pinecone;
using Pinecone.Grpc;
using Sdk = Pinecone;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Service for storing and retrieving vector records, that uses Pinecone as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public class PineconeVectorStoreRecordCollection<TRecord> : IVectorStoreRecordCollection<string, TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    private const string DatabaseName = "Pinecone";
    private const string CreateCollectionName = "CreateCollection";
    private const string CollectionExistsName = "CollectionExists";
    private const string DeleteCollectionName = "DeleteCollection";

    private const string UpsertOperationName = "Upsert";
    private const string DeleteOperationName = "Delete";
    private const string GetOperationName = "Get";
    private const string QueryOperationName = "Query";

    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    private readonly Sdk.PineconeClient _pineconeClient;
    private readonly PineconeVectorStoreRecordCollectionOptions<TRecord> _options;
    private readonly VectorStoreRecordPropertyReader _propertyReader;
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
        Verify.NotNullOrWhiteSpace(collectionName);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelKeyType(typeof(TRecord), options?.VectorCustomMapper is not null, PineconeVectorStoreRecordFieldMapping.s_supportedKeyTypes);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelDefinitionSupplied(typeof(TRecord), options?.VectorStoreRecordDefinition is not null);

        this._pineconeClient = pineconeClient;
        this.CollectionName = collectionName;
        this._options = options ?? new PineconeVectorStoreRecordCollectionOptions<TRecord>();
        this._propertyReader = new VectorStoreRecordPropertyReader(
            typeof(TRecord),
            this._options.VectorStoreRecordDefinition,
            new()
            {
                RequiresAtLeastOneVector = true,
                SupportsMultipleKeys = false,
                SupportsMultipleVectors = false,
            });

        if (this._options.VectorCustomMapper is not null)
        {
            // Custom Mapper.
            this._mapper = this._options.VectorCustomMapper;
        }
        else if (typeof(TRecord) == typeof(VectorStoreGenericDataModel<string>))
        {
            // Generic data model mapper.
            this._mapper = (new PineconeGenericDataModelMapper(this._propertyReader) as IVectorStoreRecordMapper<TRecord, Sdk.Vector>)!;
        }
        else
        {
            // Default Mapper.
            this._mapper = new PineconeVectorStoreRecordMapper<TRecord>(this._propertyReader);
        }
    }

    /// <inheritdoc />
    public virtual async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
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
    public virtual async Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        // we already run through record property validation, so a single VectorStoreRecordVectorProperty is guaranteed.
        var vectorProperty = this._propertyReader.VectorProperty!;
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
    public virtual async Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        if (!await this.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
        {
            await this.CreateCollectionAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public virtual Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
        => this.RunOperationAsync(
            DeleteCollectionName,
            () => this._pineconeClient.DeleteIndex(this.CollectionName, cancellationToken));

    /// <inheritdoc />
    public virtual async Task<TRecord?> GetAsync(string key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        var records = await this.GetBatchAsync([key], options, cancellationToken).ToListAsync(cancellationToken).ConfigureAwait(false);

        return records.FirstOrDefault();
    }

    /// <inheritdoc />
    public virtual async IAsyncEnumerable<TRecord> GetBatchAsync(
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
            () => results.Values.Select(x => this._mapper.MapFromStorageToDataModel(x, mapperOptions)));

        foreach (var record in records)
        {
            yield return record;
        }
    }

    /// <inheritdoc />
    public virtual Task DeleteAsync(string key, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(key);

        return this.DeleteBatchAsync([key], cancellationToken);
    }

    /// <inheritdoc />
    public virtual async Task DeleteBatchAsync(IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        var indexNamespace = this.GetIndexNamespace();

        var index = await this.GetIndexAsync(this.CollectionName, cancellationToken).ConfigureAwait(false);

        await this.RunOperationAsync(
            DeleteOperationName,
            () => index.Delete(keys, indexNamespace, cancellationToken)).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public virtual async Task<string> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
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
    public virtual async IAsyncEnumerable<string> UpsertBatchAsync(IEnumerable<TRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
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

    /// <inheritdoc />
    public virtual async Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(vector);

        if (vector is not ReadOnlyMemory<float> floatVector)
        {
            throw new NotSupportedException($"The provided vector type {vector.GetType().FullName} is not supported by the Pinecone connector." +
                $"Supported types are: {typeof(ReadOnlyMemory<float>).FullName}");
        }

        // Resolve options and build filter clause.
        var internalOptions = options ?? s_defaultVectorSearchOptions;
        var mapperOptions = new StorageToDataModelMapperOptions { IncludeVectors = options?.IncludeVectors ?? false };

#pragma warning disable CS0618 // FilterClause is obsolete
        var filter = PineconeVectorStoreCollectionSearchMapping.BuildSearchFilter(
            internalOptions.OldFilter?.FilterClauses,
            this._propertyReader.StoragePropertyNamesMap);
#pragma warning restore CS0618

        // Get the current index.
        var indexNamespace = this.GetIndexNamespace();
        var index = await this.GetIndexAsync(this.CollectionName, cancellationToken).ConfigureAwait(false);

        // Search.
        var results = await this.RunOperationAsync(
            QueryOperationName,
            () => index.Query(
                floatVector.ToArray(),
                (uint)(internalOptions.Skip + internalOptions.Top),
                filter,
                sparseValues: null,
                indexNamespace,
                internalOptions.IncludeVectors,
                includeMetadata: true,
                cancellationToken)).ConfigureAwait(false);

        // Skip the required results for paging.
        var skippedResults = results.Skip(internalOptions.Skip);

        // Map the results.
        var records = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this.CollectionName,
            QueryOperationName,
            () =>
            {
                // First convert to Vector objects, since the
                // mapper requires these as input.
                var vectorResults = skippedResults.Select(x => (
                    Vector: new Vector()
                    {
                        Id = x.Id,
                        Values = x.Values ?? Array.Empty<float>(),
                        Metadata = x.Metadata,
                        SparseValues = x.SparseValues
                    },
                    x.Score));

                return vectorResults.Select(x => new VectorSearchResult<TRecord>(
                    this._mapper.MapFromStorageToDataModel(x.Vector, mapperOptions),
                    x.Score));
            });

        return new VectorSearchResults<TRecord>(records.ToAsyncEnumerable());
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
