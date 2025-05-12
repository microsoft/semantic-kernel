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
using Microsoft.Extensions.VectorData.ProviderServices;
using Npgsql;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

/// <summary>
/// Represents a collection of vector store records in a Postgres database.
/// </summary>
/// <typeparam name="TKey">The type of the key.</typeparam>
/// <typeparam name="TRecord">The type of the record.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class PostgresCollection<TKey, TRecord> : VectorStoreCollection<TKey, TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
    where TKey : notnull
    where TRecord : class
{
    /// <inheritdoc />
    public override string Name { get; }

    /// <summary>Metadata about vector store record collection.</summary>
    private readonly VectorStoreCollectionMetadata _collectionMetadata;

    /// <summary>Postgres client that is used to interact with the database.</summary>
    private readonly PostgresDbClient _client;

    /// <summary>The model for this collection.</summary>
    private readonly CollectionModel _model;

    /// <summary>A mapper to use for converting between the data model and the Azure AI Search record.</summary>
    private readonly PostgresMapper<TRecord> _mapper;

    /// <summary>The default options for vector search.</summary>
    private static readonly RecordSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="dataSource">The data source to use for connecting to the database.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="ownsDataSource">A value indicating whether the data source must be disposed after the collection is disposed.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public PostgresCollection(NpgsqlDataSource dataSource, string name, bool ownsDataSource, PostgresCollectionOptions? options = default)
        : this(new PostgresDbClient(dataSource, options?.Schema, ownsDataSource), name, options)
    {
        Verify.NotNull(dataSource);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="connectionString">Postgres database connection string.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public PostgresCollection(string connectionString, string name, PostgresCollectionOptions? options = default)
#pragma warning disable CA2000 // Dispose objects before losing scope
        : this(PostgresUtils.CreateDataSource(connectionString), name, ownsDataSource: true, options)
#pragma warning restore CA2000 // Dispose objects before losing scope
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="client">The client to use for interacting with the database.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <remarks>
    /// This constructor is internal. It allows internal code to create an instance of this class with a custom client.
    /// </remarks>
    internal PostgresCollection(PostgresDbClient client, string name, PostgresCollectionOptions? options = default)
    {
        // Verify.
        Verify.NotNull(client);
        Verify.NotNullOrWhiteSpace(name);

        // Assign.
        this._client = client;
        this.Name = name;

        this._model = new PostgresModelBuilder()
            .Build(typeof(TRecord), options?.VectorStoreRecordDefinition, options?.EmbeddingGenerator);

        this._mapper = new PostgresMapper<TRecord>(this._model);

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = PostgresConstants.VectorStoreSystemName,
            VectorStoreName = this._client.DatabaseName,
            CollectionName = name
        };
    }

    /// <inheritdoc />
    protected override void Dispose(bool disposing)
    {
        this._client.Dispose();
        base.Dispose(disposing);
    }

    /// <inheritdoc/>
    public override Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "DoesTableExists";
        return this.RunOperationAsync(OperationName, () =>
            this._client.DoesTableExistsAsync(this.Name, cancellationToken)
        );
    }

    /// <inheritdoc/>
    public override Task EnsureCollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "EnsureCollectionExists";
        return this.RunOperationAsync(OperationName, () =>
            this.InternalCreateCollectionAsync(true, cancellationToken)
        );
    }

    /// <inheritdoc/>
    public override Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "DeleteCollection";
        return this.RunOperationAsync(OperationName, () =>
            this._client.DeleteTableAsync(this.Name, cancellationToken)
        );
    }

    /// <inheritdoc/>
    public override async Task UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
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
#if NET8_0_OR_GREATER
            else if (vectorProperty.TryGenerateEmbedding<TRecord, Embedding<Half>, ReadOnlyMemory<Half>>(record, cancellationToken, out var halfTask))
            {
                generatedEmbeddings ??= new IReadOnlyList<Embedding>?[vectorPropertyCount];
                generatedEmbeddings[i] = [await halfTask.ConfigureAwait(false)];
            }
#endif
            else
            {
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{vectorProperty.ModelName}' cannot produce an embedding of type '{typeof(Embedding<float>).Name}' for the given input type.");
            }
        }

        var storageModel = this._mapper.MapFromDataToStorageModel(record, recordIndex: 0, generatedEmbeddings);

        Verify.NotNull(storageModel);

        var keyObj = storageModel[this._model.KeyProperty.StorageName];
        Verify.NotNull(keyObj);
        TKey key = (TKey)keyObj!;

        await this.RunOperationAsync(OperationName, async () =>
            await this._client.UpsertAsync(this.Name, storageModel, this._model.KeyProperty.StorageName, cancellationToken).ConfigureAwait(false))
            .ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public override async Task UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
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
                    return;
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
#if NET8_0_OR_GREATER
            else if (vectorProperty.TryGenerateEmbeddings<TRecord, Embedding<Half>, ReadOnlyMemory<Half>>(records, cancellationToken, out var halfTask))
            {
                generatedEmbeddings ??= new IReadOnlyList<Embedding>?[vectorPropertyCount];
                generatedEmbeddings[i] = (IReadOnlyList<Embedding<Half>>)await halfTask.ConfigureAwait(false);
            }
#endif
            else
            {
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{vectorProperty.ModelName}' cannot produce an embedding of type '{typeof(Embedding<float>).Name}' for the given input type.");
            }
        }

        var storageModels = records.Select((r, i) => this._mapper.MapFromDataToStorageModel(r, i, generatedEmbeddings)).ToList();

        if (storageModels.Count == 0)
        {
            return;
        }

        var keys = storageModels.Select(model => model[this._model.KeyProperty.StorageName]!).ToList();

        await this.RunOperationAsync(OperationName, () =>
            this._client.UpsertBatchAsync(this.Name, storageModels, this._model.KeyProperty.StorageName, cancellationToken)
        ).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public override Task<TRecord?> GetAsync(TKey key, RecordRetrievalOptions? options = null, CancellationToken cancellationToken = default)
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
            return this._mapper.MapFromStorageToDataModel(row, includeVectors);
        });
    }

    /// <inheritdoc/>
    public override IAsyncEnumerable<TRecord> GetAsync(IEnumerable<TKey> keys, RecordRetrievalOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "GetBatch";

        Verify.NotNull(keys);

        bool includeVectors = options?.IncludeVectors is true;

        if (includeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        return PostgresUtils.WrapAsyncEnumerableAsync(
            this._client.GetBatchAsync(this.Name, keys, this._model, includeVectors, cancellationToken)
                .SelectAsync(row =>
                    this._mapper.MapFromStorageToDataModel(row, includeVectors),
                    cancellationToken
                ),
            OperationName,
            this._collectionMetadata
        );
    }

    /// <inheritdoc/>
    public override Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        const string OperationName = "Delete";
        return this.RunOperationAsync(OperationName, () =>
            this._client.DeleteAsync(this.Name, this._model.KeyProperty.StorageName, key, cancellationToken)
        );
    }

    /// <inheritdoc/>
    public override Task DeleteAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        const string OperationName = "DeleteBatch";
        return this.RunOperationAsync(OperationName, () =>
            this._client.DeleteBatchAsync(this.Name, this._model.KeyProperty.StorageName, keys, cancellationToken)
        );
    }

    #region Search

    /// <inheritdoc />
    public override async IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TInput>(
        TInput value,
        int top,
        RecordSearchOptions<TRecord>? options = default,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        options ??= s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        switch (vectorProperty.EmbeddingGenerator)
        {
            case IEmbeddingGenerator<TInput, Embedding<float>> generator:
            {
                var embedding = await generator.GenerateEmbeddingAsync(value, new() { Dimensions = vectorProperty.Dimensions }, cancellationToken).ConfigureAwait(false);

                await foreach (var record in this.SearchCoreAsync(embedding.Vector, top, vectorProperty, operationName: "Search", options, cancellationToken).ConfigureAwait(false))
                {
                    yield return record;
                }

                yield break;
            }

#if NET8_0_OR_GREATER
            case IEmbeddingGenerator<TInput, Embedding<Half>> generator:
            {
                var embedding = await generator.GenerateEmbeddingAsync(value, new() { Dimensions = vectorProperty.Dimensions }, cancellationToken).ConfigureAwait(false);

                await foreach (var record in this.SearchCoreAsync(embedding.Vector, top, vectorProperty, operationName: "Search", options, cancellationToken).ConfigureAwait(false))
                {
                    yield return record;
                }

                yield break;
            }
#endif

            case null:
                throw new InvalidOperationException(VectorDataStrings.NoEmbeddingGeneratorWasConfiguredForSearch);

            default:
                throw new InvalidOperationException(
                    PostgresModelBuilder.SupportedVectorTypes.Contains(typeof(TInput))
                        ? VectorDataStrings.EmbeddingTypePassedToSearchAsync
                        : VectorDataStrings.IncompatibleEmbeddingGeneratorWasConfiguredForInputType(typeof(TInput), vectorProperty.EmbeddingGenerator.GetType()));
        }
    }

    /// <inheritdoc />
    public override IAsyncEnumerable<VectorSearchResult<TRecord>> SearchEmbeddingAsync<TVector>(
        TVector vector,
        int top,
        RecordSearchOptions<TRecord>? options = null,
        CancellationToken cancellationToken = default)
    {
        options ??= s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        return this.SearchCoreAsync(vector, top, vectorProperty, operationName: "SearchEmbedding", options, cancellationToken);
    }

    private IAsyncEnumerable<VectorSearchResult<TRecord>> SearchCoreAsync<TVector>(
        TVector vector,
        int top,
        VectorPropertyModel vectorProperty,
        string operationName,
        RecordSearchOptions<TRecord> options,
        CancellationToken cancellationToken = default)
        where TVector : notnull
    {
        Verify.NotNull(vector);
        Verify.NotLessThan(top, 1);

        var vectorType = vector.GetType();

        if (!PostgresModelBuilder.SupportedVectorTypes.Contains(vectorType))
        {
            throw new NotSupportedException(
                $"The provided vector type {vectorType.Name} is not supported by the PostgreSQL connector. " +
                $"Supported types are: {string.Join(", ", PostgresModelBuilder.SupportedVectorTypes.Select(l => l.Name))}");
        }

        if (options.IncludeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        var pgVector = PostgresPropertyMapping.MapVectorForStorageModel(vector);

        Verify.NotNull(pgVector);

        // Simulating skip/offset logic locally, since OFFSET can work only with LIMIT in combination
        // and LIMIT is not supported in vector search extension, instead of LIMIT - "k" parameter is used.
        var limit = top + options.Skip;

        return PostgresUtils.WrapAsyncEnumerableAsync(
            this._client.GetNearestMatchesAsync(this.Name, this._model, vectorProperty, pgVector, top, options, cancellationToken)
                .SelectAsync(result =>
                {
                    var record = this._mapper.MapFromStorageToDataModel(result.Row, options.IncludeVectors);

                    return new VectorSearchResult<TRecord>(record, result.Distance);
                }, cancellationToken),
            operationName,
            this._collectionMetadata
        );
    }

    #endregion Search

    /// <inheritdoc />
    public override IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top,
        FilteredRecordRetrievalOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(filter);
        Verify.NotLessThan(top, 1);

        options ??= new();

        return PostgresUtils.WrapAsyncEnumerableAsync(
            this._client.GetMatchingRecordsAsync(this.Name, this._model, filter, top, options, cancellationToken)
                .SelectAsync(dictionary =>
                {
                    return this._mapper.MapFromStorageToDataModel(dictionary, options.IncludeVectors);
                }, cancellationToken),
            "Get",
            this._collectionMetadata);
    }

    /// <inheritdoc />
    public override object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreCollectionMetadata) ? this._collectionMetadata :
            serviceType == typeof(NpgsqlDataSource) ? this._client.DataSource :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }

    private Task InternalCreateCollectionAsync(bool ifNotExists, CancellationToken cancellationToken = default)
    {
        return this._client.CreateTableAsync(this.Name, this._model, ifNotExists, cancellationToken);
    }

    private Task RunOperationAsync(string operationName, Func<Task> operation)
        => VectorStoreErrorHandler.RunOperationAsync<NpgsqlException>(
            this._collectionMetadata,
            operationName,
            operation);

    private Task<T> RunOperationAsync<T>(string operationName, Func<Task<T>> operation)
        => VectorStoreErrorHandler.RunOperationAsync<T, NpgsqlException>(
            this._collectionMetadata,
            operationName,
            operation);
}
