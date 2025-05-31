// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Npgsql;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

/// <summary>
/// Represents a collection of vector store records in a Postgres database.
/// </summary>
/// <typeparam name="TKey">The type of the key.</typeparam>
/// <typeparam name="TRecord">The type of the record.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public class PostgresCollection<TKey, TRecord> : VectorStoreCollection<TKey, TRecord>
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
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="dataSource">The data source to use for connecting to the database.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="ownsDataSource">A value indicating whether <paramref name="dataSource"/> is disposed when the collection is disposed.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    [RequiresDynamicCode("This constructor is incompatible with NativeAOT. For dynamic mapping via Dictionary<string, object?>, instantiate PostgresDynamicCollection instead.")]
    [RequiresUnreferencedCode("This constructor is incompatible with trimming. For dynamic mapping via Dictionary<string, object?>, instantiate PostgresDynamicCollection instead")]
    public PostgresCollection(NpgsqlDataSource dataSource, string name, bool ownsDataSource, PostgresCollectionOptions? options = default)
        : this(() => new PostgresDbClient(dataSource, options?.Schema, ownsDataSource), name, options)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="connectionString">Postgres database connection string.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    [RequiresDynamicCode("This constructor is incompatible with NativeAOT. For dynamic mapping via Dictionary<string, object?>, instantiate PostgresDynamicCollection instead.")]
    [RequiresUnreferencedCode("This constructor is incompatible with trimming. For dynamic mapping via Dictionary<string, object?>, instantiate PostgresDynamicCollection instead")]
    public PostgresCollection(string connectionString, string name, PostgresCollectionOptions? options = default)
        : this(() => new PostgresDbClient(PostgresUtils.CreateDataSource(connectionString), options?.Schema, ownsDataSource: true), name, options)
    {
        Verify.NotNullOrWhiteSpace(connectionString);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="clientFactory">The client to use for interacting with the database.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <remarks>
    /// This constructor is internal. It allows internal code to create an instance of this class with a custom client.
    /// </remarks>
    [RequiresDynamicCode("This constructor is incompatible with NativeAOT. For dynamic mapping via Dictionary<string, object?>, instantiate PostgresDynamicCollection instead.")]
    [RequiresUnreferencedCode("This constructor is incompatible with trimming. For dynamic mapping via Dictionary<string, object?>, instantiate PostgresDynamicCollection instead.")]
    internal PostgresCollection(Func<PostgresDbClient> clientFactory, string name, PostgresCollectionOptions? options)
        : this(
            clientFactory,
            name,
            static options => typeof(TRecord) == typeof(Dictionary<string, object?>)
                ? throw new NotSupportedException(VectorDataStrings.NonDynamicCollectionWithDictionaryNotSupported(typeof(PostgresDynamicCollection)))
                : new PostgresModelBuilder().Build(typeof(TRecord), options.Definition, options.EmbeddingGenerator),
            options)
    {
    }

    internal PostgresCollection(Func<PostgresDbClient> clientFactory, string name, Func<PostgresCollectionOptions, CollectionModel> modelFactory, PostgresCollectionOptions? options)
    {
        Verify.NotNullOrWhiteSpace(name);

        options ??= PostgresCollectionOptions.Default;

        this.Name = name;
        this._model = modelFactory(options);
        this._mapper = new PostgresMapper<TRecord>(this._model);

        // The code above can throw, so we need to create the client after the model is built and verified.
        // In case an exception is thrown, we don't need to dispose any resources.
        this._client = clientFactory();

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
    public override Task EnsureCollectionDeletedAsync(CancellationToken cancellationToken = default)
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

            if (PostgresModelBuilder.IsVectorPropertyTypeValidCore(vectorProperty.Type, out _))
            {
                continue;
            }

            // We have a vector property whose type isn't natively supported - we need to generate embeddings.
            Debug.Assert(vectorProperty.EmbeddingGenerator is not null);

            // TODO: Ideally we'd group together vector properties using the same generator (and with the same input and output properties),
            // and generate embeddings for them in a single batch. That's some more complexity though.
            if (vectorProperty.TryGenerateEmbedding<TRecord, Embedding<float>>(record, cancellationToken, out var floatTask))
            {
                generatedEmbeddings ??= new IReadOnlyList<Embedding>?[vectorPropertyCount];
                generatedEmbeddings[i] = [await floatTask.ConfigureAwait(false)];
            }
#if NET8_0_OR_GREATER
            else if (vectorProperty.TryGenerateEmbedding<TRecord, Embedding<Half>>(record, cancellationToken, out var halfTask))
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

            if (PostgresModelBuilder.IsVectorPropertyTypeValidCore(vectorProperty.Type, out _))
            {
                continue;
            }

            // We have a vector property whose type isn't natively supported - we need to generate embeddings.
            Debug.Assert(vectorProperty.EmbeddingGenerator is not null);

            // Materialize the records' enumerable if needed, to prevent multiple enumeration.
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
            if (vectorProperty.TryGenerateEmbeddings<TRecord, Embedding<float>>(records, cancellationToken, out var floatTask))
            {
                generatedEmbeddings ??= new IReadOnlyList<Embedding>?[vectorPropertyCount];
                generatedEmbeddings[i] = (IReadOnlyList<Embedding<float>>)await floatTask.ConfigureAwait(false);
            }
#if NET8_0_OR_GREATER
            else if (vectorProperty.TryGenerateEmbeddings<TRecord, Embedding<Half>>(records, cancellationToken, out var halfTask))
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
        if (includeVectors && this._model.EmbeddingGenerationRequired)
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
        if (includeVectors && this._model.EmbeddingGenerationRequired)
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
        TInput searchValue,
        int top,
        VectorSearchOptions<TRecord>? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(searchValue);
        Verify.NotLessThan(top, 1);

        options ??= s_defaultVectorSearchOptions;
        if (options.IncludeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        object vector = searchValue switch
        {
            // Dense float32
            ReadOnlyMemory<float> r => r,
            float[] f => new ReadOnlyMemory<float>(f),
            Embedding<float> e => e.Vector,
            _ when vectorProperty.EmbeddingGenerator is IEmbeddingGenerator<TInput, Embedding<float>> generator
                => await generator.GenerateVectorAsync(searchValue, cancellationToken: cancellationToken).ConfigureAwait(false),

#if NET8_0_OR_GREATER
            // Dense float16
            ReadOnlyMemory<Half> r => r,
            Half[] f => new ReadOnlyMemory<Half>(f),
            Embedding<Half> e => e.Vector,
            _ when vectorProperty.EmbeddingGenerator is IEmbeddingGenerator<TInput, Embedding<Half>> generator
                => await generator.GenerateVectorAsync(searchValue, cancellationToken: cancellationToken).ConfigureAwait(false),
#endif

            // Dense Binary
            BitArray b => b,
            // TODO: Uncomment once we sync to the latest MEAI
            // BinaryEmbedding e => e.Vector,
            // _ when vectorProperty.EmbeddingGenerator is IEmbeddingGenerator<TVector, BinaryEmbedding> generator
            //     => (await generator.GenerateEmbeddingAsync(value, cancellationToken: cancellationToken).ConfigureAwait(false)).Vector,

            // Sparse
            SparseVector sv => sv,
            // TODO: Add a PG-specific SparseVectorEmbedding type

            _ => vectorProperty.EmbeddingGenerator is null
                ? throw new NotSupportedException(VectorDataStrings.InvalidSearchInputAndNoEmbeddingGeneratorWasConfigured(searchValue.GetType(), PostgresModelBuilder.SupportedVectorTypes))
                : throw new InvalidOperationException(VectorDataStrings.IncompatibleEmbeddingGeneratorWasConfiguredForInputType(typeof(TInput), vectorProperty.EmbeddingGenerator.GetType()))
        };

        var pgVector = PostgresPropertyMapping.MapVectorForStorageModel(vector);

        Verify.NotNull(pgVector);

        // Simulating skip/offset logic locally, since OFFSET can work only with LIMIT in combination
        // and LIMIT is not supported in vector search extension, instead of LIMIT - "k" parameter is used.
        var limit = top + options.Skip;

        var records = PostgresUtils.WrapAsyncEnumerableAsync(
            this._client
                .GetNearestMatchesAsync(this.Name, this._model, vectorProperty, pgVector, top, options, cancellationToken)
                .SelectAsync(result => new VectorSearchResult<TRecord>(
                    this._mapper.MapFromStorageToDataModel(result.Row, options.IncludeVectors),
                    result.Distance),
                cancellationToken),
            operationName: "Search",
            this._collectionMetadata)
            .ConfigureAwait(false);

        await foreach (var record in records)
        {
            yield return record;
        }
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
