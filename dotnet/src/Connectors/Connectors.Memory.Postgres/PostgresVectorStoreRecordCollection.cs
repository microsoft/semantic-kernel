// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Microsoft.Extensions.VectorData.Properties;
using Npgsql;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// Represents a collection of vector store records in a Postgres database.
/// </summary>
/// <typeparam name="TKey">The type of the key.</typeparam>
/// <typeparam name="TRecord">The type of the record.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class PostgresVectorStoreRecordCollection<TKey, TRecord> : IVectorStoreRecordCollection<TKey, TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
    where TKey : notnull
    where TRecord : notnull
{
    /// <inheritdoc />
    public string Name { get; }

    /// <summary>Metadata about vector store record collection.</summary>
    private readonly VectorStoreRecordCollectionMetadata _collectionMetadata;

    /// <summary>Postgres client that is used to interact with the database.</summary>
    private readonly IPostgresVectorStoreDbClient _client;

    // <summary>Optional configuration options for this class.</summary>
    private readonly PostgresVectorStoreRecordCollectionOptions<TRecord> _options;

    /// <summary>The model for this collection.</summary>
    private readonly VectorStoreRecordModel _model;

    /// <summary>A mapper to use for converting between the data model and the Azure AI Search record.</summary>
    private readonly PostgresVectorStoreRecordMapper<TRecord> _mapper;

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="dataSource">The data source to use for connecting to the database.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public PostgresVectorStoreRecordCollection(NpgsqlDataSource dataSource, string name, PostgresVectorStoreRecordCollectionOptions<TRecord>? options = default)
        : this(new PostgresVectorStoreDbClient(dataSource), name, options)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="client">The client to use for interacting with the database.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <remarks>
    /// This constructor is internal. It allows internal code to create an instance of this class with a custom client.
    /// </remarks>
    internal PostgresVectorStoreRecordCollection(IPostgresVectorStoreDbClient client, string name, PostgresVectorStoreRecordCollectionOptions<TRecord>? options = default)
    {
        // Verify.
        Verify.NotNull(client);
        Verify.NotNullOrWhiteSpace(name);

        // Assign.
        this._client = client;
        this.Name = name;
        this._options = options ?? new PostgresVectorStoreRecordCollectionOptions<TRecord>();

        this._model = new VectorStoreRecordModelBuilder(PostgresConstants.ModelBuildingOptions)
            .Build(typeof(TRecord), options?.VectorStoreRecordDefinition, options?.EmbeddingGenerator);

        this._mapper = new PostgresVectorStoreRecordMapper<TRecord>(this._model);

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = PostgresConstants.VectorStoreSystemName,
            VectorStoreName = this._client.DatabaseName,
            CollectionName = name
        };
    }

    /// <inheritdoc/>
    public Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "DoesTableExists";
        return this.RunOperationAsync(OperationName, () =>
            this._client.DoesTableExistsAsync(this.Name, cancellationToken)
        );
    }

    /// <inheritdoc/>
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "CreateCollection";
        return this.RunOperationAsync(OperationName, () =>
            this.InternalCreateCollectionAsync(false, cancellationToken)
        );
    }

    /// <inheritdoc/>
    public Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "CreateCollectionIfNotExists";
        return this.RunOperationAsync(OperationName, () =>
            this.InternalCreateCollectionAsync(true, cancellationToken)
        );
    }

    /// <inheritdoc/>
    public Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "DeleteCollection";
        return this.RunOperationAsync(OperationName, () =>
            this._client.DeleteTableAsync(this.Name, cancellationToken)
        );
    }

    /// <inheritdoc/>
    public async Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        const string OperationName = "Upsert";

        IReadOnlyList<Embedding>?[]? generatedEmbeddings = null;

        var vectorPropertyCount = this._model.VectorProperties.Count;
        for (var i = 0; i < vectorPropertyCount; i++)
        {
            var vectorProperty = this._model.VectorProperties[i];

            if (vectorProperty.EmbeddingGenerator is null)
            {
                continue;
            }

            // TODO: Ideally we'd group together vector properties using the same generator (and with the same input and output properties),
            // and generate embeddings for them in a single batch. That's some more complexity though.
            if (vectorProperty.TryGenerateEmbedding<TRecord, Embedding<float>, ReadOnlyMemory<float>>(record, cancellationToken, out var floatTask))
            {
                generatedEmbeddings ??= new IReadOnlyList<Embedding>?[vectorPropertyCount];
                generatedEmbeddings[i] = [await floatTask.ConfigureAwait(false)];
            }
            else
            {
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{vectorProperty.ModelName}' cannot produce an embedding of type '{typeof(Embedding<float>).Name}' for the given input type.");
            }
        }

        var storageModel = VectorStoreErrorHandler.RunModelConversion(
            PostgresConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this.Name,
            OperationName,
            () => this._mapper.MapFromDataToStorageModel(record, recordIndex: 0, generatedEmbeddings));

        Verify.NotNull(storageModel);

        var keyObj = storageModel[this._model.KeyProperty.StorageName];
        Verify.NotNull(keyObj);
        TKey key = (TKey)keyObj!;

        return await this.RunOperationAsync(OperationName, async () =>
            {
                await this._client.UpsertAsync(this.Name, storageModel, this._model.KeyProperty.StorageName, cancellationToken).ConfigureAwait(false);
                return key;
            }).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<TKey>> UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        const string OperationName = "UpsertBatch";

        IReadOnlyList<TRecord>? recordsList = null;

        // If an embedding generator is defined, invoke it once per property for all records.
        IReadOnlyList<Embedding>?[]? generatedEmbeddings = null;

        var vectorPropertyCount = this._model.VectorProperties.Count;
        for (var i = 0; i < vectorPropertyCount; i++)
        {
            var vectorProperty = this._model.VectorProperties[i];

            if (vectorProperty.EmbeddingGenerator is null)
            {
                continue;
            }

            // We have a property with embedding generation; materialize the records' enumerable if needed, to
            // prevent multiple enumeration.
            if (recordsList is null)
            {
                recordsList = records is IReadOnlyList<TRecord> r ? r : records.ToList();

                if (recordsList.Count == 0)
                {
                    return [];
                }

                records = recordsList;
            }

            // TODO: Ideally we'd group together vector properties using the same generator (and with the same input and output properties),
            // and generate embeddings for them in a single batch. That's some more complexity though.
            if (vectorProperty.TryGenerateEmbeddings<TRecord, Embedding<float>, ReadOnlyMemory<float>>(records, cancellationToken, out var floatTask))
            {
                generatedEmbeddings ??= new IReadOnlyList<Embedding>?[vectorPropertyCount];
                generatedEmbeddings[i] = (IReadOnlyList<Embedding<float>>)await floatTask.ConfigureAwait(false);
            }
            else
            {
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{vectorProperty.ModelName}' cannot produce an embedding of type '{typeof(Embedding<float>).Name}' for the given input type.");
            }
        }

        var storageModels = VectorStoreErrorHandler.RunModelConversion(
            PostgresConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this.Name,
            OperationName,
            () => records.Select((r, i) => this._mapper.MapFromDataToStorageModel(r, i, generatedEmbeddings)).ToList());

        if (storageModels.Count == 0)
        {
            return [];
        }

        var keys = storageModels.Select(model => model[this._model.KeyProperty.StorageName]!).ToList();

        await this.RunOperationAsync(OperationName, () =>
            this._client.UpsertBatchAsync(this.Name, storageModels, this._model.KeyProperty.StorageName, cancellationToken)
        ).ConfigureAwait(false);

        return keys.Select(key => (TKey)key!).ToList();
    }

    /// <inheritdoc/>
    public Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "Get";

        Verify.NotNull(key);

        bool includeVectors = options?.IncludeVectors is true;

        if (includeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        return this.RunOperationAsync<TRecord?>(OperationName, async () =>
        {
            var row = await this._client.GetAsync(this.Name, key, this._model, includeVectors, cancellationToken).ConfigureAwait(false);

            if (row is null) { return default; }
            return VectorStoreErrorHandler.RunModelConversion(
                PostgresConstants.VectorStoreSystemName,
                this._collectionMetadata.VectorStoreName,
                this.Name,
                OperationName,
                () => this._mapper.MapFromStorageToDataModel(row, new() { IncludeVectors = includeVectors }));
        });
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<TRecord> GetAsync(IEnumerable<TKey> keys, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "GetBatch";

        Verify.NotNull(keys);

        bool includeVectors = options?.IncludeVectors is true;

        if (includeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        return PostgresVectorStoreUtils.WrapAsyncEnumerableAsync(
            this._client.GetBatchAsync(this.Name, keys, this._model, includeVectors, cancellationToken)
                .SelectAsync(row =>
                    VectorStoreErrorHandler.RunModelConversion(
                        PostgresConstants.VectorStoreSystemName,
                        this._collectionMetadata.VectorStoreName,
                        this.Name,
                        OperationName,
                        () => this._mapper.MapFromStorageToDataModel(row, new() { IncludeVectors = includeVectors })),
                    cancellationToken
                ),
            OperationName,
            this._collectionMetadata.VectorStoreName,
            this.Name
        );
    }

    /// <inheritdoc/>
    public Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        const string OperationName = "Delete";
        return this.RunOperationAsync(OperationName, () =>
            this._client.DeleteAsync(this.Name, this._model.KeyProperty.StorageName, key, cancellationToken)
        );
    }

    /// <inheritdoc/>
    public Task DeleteAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        const string OperationName = "DeleteBatch";
        return this.RunOperationAsync(OperationName, () =>
            this._client.DeleteBatchAsync(this.Name, this._model.KeyProperty.StorageName, keys, cancellationToken)
        );
    }

    #region Search

    /// <inheritdoc />
    public async IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TInput>(
        TInput value,
        int top,
        VectorSearchOptions<TRecord>? options = default,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
        where TInput : notnull
    {
        options ??= s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        switch (vectorProperty.EmbeddingGenerator)
        {
            case IEmbeddingGenerator<TInput, Embedding<float>> generator:
                var embedding = await generator.GenerateAsync(value, new() { Dimensions = vectorProperty.Dimensions }, cancellationToken).ConfigureAwait(false);

                await foreach (var record in this.SearchCoreAsync(embedding.Vector, top, vectorProperty, operationName: "Search", options, cancellationToken).ConfigureAwait(false))
                {
                    yield return record;
                }

                yield break;

            // TODO: Implement support for Half, binary, sparse embeddings (#11083)

            case null:
                throw new InvalidOperationException(VectorDataStrings.NoEmbeddingGeneratorWasConfiguredForSearch);

            default:
                throw new InvalidOperationException(
                    PostgresConstants.SupportedVectorTypes.Contains(typeof(TInput))
                        ? string.Format(VectorDataStrings.EmbeddingTypePassedToSearchAsync)
                        : string.Format(VectorDataStrings.IncompatibleEmbeddingGeneratorWasConfiguredForInputType, typeof(TInput).Name, vectorProperty.EmbeddingGenerator.GetType().Name));
        }
    }

    /// <inheritdoc />
    public IAsyncEnumerable<VectorSearchResult<TRecord>> SearchEmbeddingAsync<TVector>(
        TVector vector,
        int top,
        VectorSearchOptions<TRecord>? options = null,
        CancellationToken cancellationToken = default)
        where TVector : notnull
    {
        options ??= s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        return this.SearchCoreAsync(vector, top, vectorProperty, operationName: "SearchEmbedding", options, cancellationToken);
    }

    private IAsyncEnumerable<VectorSearchResult<TRecord>> SearchCoreAsync<TVector>(
        TVector vector,
        int top,
        VectorStoreRecordVectorPropertyModel vectorProperty,
        string operationName,
        VectorSearchOptions<TRecord> options,
        CancellationToken cancellationToken = default)
        where TVector : notnull
    {
        Verify.NotNull(vector);
        Verify.NotLessThan(top, 1);

        var vectorType = vector.GetType();

        if (!PostgresConstants.SupportedVectorTypes.Contains(vectorType))
        {
            throw new NotSupportedException(
                $"The provided vector type {vectorType.FullName} is not supported by the PostgreSQL connector. " +
                $"Supported types are: {string.Join(", ", PostgresConstants.SupportedVectorTypes.Select(l => l.FullName))}");
        }

        if (options.IncludeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        var pgVector = PostgresVectorStoreRecordPropertyMapping.MapVectorForStorageModel(vector);

        Verify.NotNull(pgVector);

        // Simulating skip/offset logic locally, since OFFSET can work only with LIMIT in combination
        // and LIMIT is not supported in vector search extension, instead of LIMIT - "k" parameter is used.
        var limit = top + options.Skip;

        StorageToDataModelMapperOptions mapperOptions = new() { IncludeVectors = options.IncludeVectors };

        return PostgresVectorStoreUtils.WrapAsyncEnumerableAsync(
            this._client.GetNearestMatchesAsync(this.Name, this._model, vectorProperty, pgVector, top, options, cancellationToken)
                .SelectAsync(result =>
                {
                    var record = VectorStoreErrorHandler.RunModelConversion(
                        PostgresConstants.VectorStoreSystemName,
                        this._collectionMetadata.VectorStoreName,
                        this.Name,
                        operationName,
                        () => this._mapper.MapFromStorageToDataModel(result.Row, mapperOptions));

                    return new VectorSearchResult<TRecord>(record, result.Distance);
                }, cancellationToken),
            operationName,
            this._collectionMetadata.VectorStoreName,
            this.Name
        );
    }

    /// <inheritdoc />
    [Obsolete("Use either SearchEmbeddingAsync to search directly on embeddings, or SearchAsync to handle embedding generation internally as part of the call.")]
    public IAsyncEnumerable<VectorSearchResult<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, int top, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
        where TVector : notnull
        => this.SearchEmbeddingAsync(vector, top, options, cancellationToken);

    #endregion Search

    /// <inheritdoc />
    public IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top,
        GetFilteredRecordOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(filter);
        Verify.NotLessThan(top, 1);

        options ??= new();

        StorageToDataModelMapperOptions mapperOptions = new() { IncludeVectors = options.IncludeVectors };

        return PostgresVectorStoreUtils.WrapAsyncEnumerableAsync(
            this._client.GetMatchingRecordsAsync(this.Name, this._model, filter, top, options, cancellationToken)
                .SelectAsync(dictionary =>
                {
                    return VectorStoreErrorHandler.RunModelConversion(
                        PostgresConstants.VectorStoreSystemName,
                        this._collectionMetadata.VectorStoreName,
                        this.Name,
                        "Get",
                        () => this._mapper.MapFromStorageToDataModel(dictionary, mapperOptions));
                }, cancellationToken),
            "Get",
            this._collectionMetadata.VectorStoreName,
            this.Name);
    }

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreRecordCollectionMetadata) ? this._collectionMetadata :
            serviceType == typeof(NpgsqlDataSource) ? this._client.DataSource :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }

    private Task InternalCreateCollectionAsync(bool ifNotExists, CancellationToken cancellationToken = default)
    {
        return this._client.CreateTableAsync(this.Name, this._model, ifNotExists, cancellationToken);
    }

    private async Task RunOperationAsync(string operationName, Func<Task> operation)
    {
        try
        {
            await operation.Invoke().ConfigureAwait(false);
        }
        catch (Exception ex) when (ex is not NotSupportedException)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = PostgresConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = operationName
            };
        }
    }

    private async Task<T> RunOperationAsync<T>(string operationName, Func<Task<T>> operation)
    {
        try
        {
            return await operation.Invoke().ConfigureAwait(false);
        }
        catch (Exception ex) when (ex is not NotSupportedException)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = PostgresConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = operationName
            };
        }
    }
}
