// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Microsoft.Extensions.VectorData.Properties;
using Pinecone;
using Sdk = Pinecone;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Service for storing and retrieving vector records, that uses Pinecone as the underlying storage.
/// </summary>
/// <typeparam name="TKey">The data type of the record key. Can be either <see cref="string"/>, or <see cref="object"/> for dynamic mapping.</typeparam>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class PineconeVectorStoreRecordCollection<TKey, TRecord> : IVectorStoreRecordCollection<TKey, TRecord>
    where TKey : notnull
    where TRecord : notnull
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>Metadata about vector store record collection.</summary>
    private readonly VectorStoreRecordCollectionMetadata _collectionMetadata;

    private readonly Sdk.PineconeClient _pineconeClient;
    private readonly PineconeVectorStoreRecordCollectionOptions<TRecord> _options;
    private readonly VectorStoreRecordModel _model;
    private readonly PineconeVectorStoreRecordMapper<TRecord> _mapper;
    private IndexClient? _indexClient;

    /// <inheritdoc />
    public string Name { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="PineconeVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="pineconeClient">Pinecone client that can be used to manage the collections and vectors in a Pinecone store.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <exception cref="ArgumentNullException">Thrown if the <paramref name="pineconeClient"/> is null.</exception>
    /// <param name="name">The name of the collection that this <see cref="PineconeVectorStoreRecordCollection{TKey, TRecord}"/> will access.</param>
    /// <exception cref="ArgumentException">Thrown for any misconfigured options.</exception>
    public PineconeVectorStoreRecordCollection(Sdk.PineconeClient pineconeClient, string name, PineconeVectorStoreRecordCollectionOptions<TRecord>? options = null)
    {
        Verify.NotNull(pineconeClient);
        VerifyCollectionName(name);

        if (typeof(TKey) != typeof(string) && typeof(TKey) != typeof(object))
        {
            throw new NotSupportedException("Only string keys are supported (and object for dynamic mapping)");
        }

        this._pineconeClient = pineconeClient;
        this.Name = name;
        this._options = options ?? new PineconeVectorStoreRecordCollectionOptions<TRecord>();
        this._model = new VectorStoreRecordModelBuilder(PineconeVectorStoreRecordFieldMapping.ModelBuildingOptions)
            .Build(typeof(TRecord), this._options.VectorStoreRecordDefinition, this._options.EmbeddingGenerator);
        this._mapper = new PineconeVectorStoreRecordMapper<TRecord>(this._model);

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = PineconeConstants.VectorStoreSystemName,
            CollectionName = name
        };
    }

    /// <inheritdoc />
    public Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
        => this.RunCollectionOperationAsync(
            "CollectionExists",
            async () =>
            {
                var collections = await this._pineconeClient.ListIndexesAsync(cancellationToken: cancellationToken).ConfigureAwait(false);

                return collections.Indexes?.Any(x => x.Name == this.Name) is true;
            });

    /// <inheritdoc />
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        // we already run through record property validation, so a single VectorStoreRecordVectorProperty is guaranteed.
        var vectorProperty = this._model.VectorProperty!;

        if (!string.IsNullOrEmpty(vectorProperty.IndexKind) && vectorProperty.IndexKind != "PGA")
        {
            throw new InvalidOperationException(
                $"IndexKind of '{vectorProperty.IndexKind}' for property '{vectorProperty.ModelName}' is not supported. Pinecone only supports 'PGA' (Pinecone Graph Algorithm), which is always enabled.");
        }

        CreateIndexRequest request = new()
        {
            Name = this.Name,
            Dimension = vectorProperty.Dimensions,
            Metric = MapDistanceFunction(vectorProperty),
            Spec = new ServerlessIndexSpec
            {
                Serverless = new ServerlessSpec
                {
                    Cloud = MapCloud(this._options.ServerlessIndexCloud),
                    Region = this._options.ServerlessIndexRegion,
                }
            },
        };

        return this.RunCollectionOperationAsync("CreateCollection",
            () => this._pineconeClient.CreateIndexAsync(request, cancellationToken: cancellationToken));
    }

    /// <inheritdoc />
    public async Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        if (!await this.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
        {
            try
            {
                await this.CreateCollectionAsync(cancellationToken).ConfigureAwait(false);
            }
            catch (VectorStoreOperationException ex) when (ex.InnerException is PineconeApiException apiEx && apiEx.InnerException is ConflictError)
            {
                // If the collection got created in the meantime, we should ignore the exception.
            }
        }
    }

    /// <inheritdoc />
    public async Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            await this._pineconeClient.DeleteIndexAsync(this.Name, cancellationToken: cancellationToken).ConfigureAwait(false);
        }
        catch (NotFoundError)
        {
            // If the collection does not exist, we should ignore the exception.
        }
        catch (PineconeApiException other)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", other)
            {
                VectorStoreSystemName = PineconeConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = "DeleteCollection"
            };
        }
    }

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        if (options?.IncludeVectors is true && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        Sdk.FetchRequest request = new()
        {
            Namespace = this._options.IndexNamespace,
            Ids = [this.GetStringKey(key)]
        };

        var response = await this.RunIndexOperationAsync(
            "Get",
            indexClient => indexClient.FetchAsync(request, cancellationToken: cancellationToken)).ConfigureAwait(false);

        var result = response.Vectors?.Values.FirstOrDefault();
        if (result is null)
        {
            return default;
        }

        StorageToDataModelMapperOptions mapperOptions = new() { IncludeVectors = options?.IncludeVectors is true };
        return VectorStoreErrorHandler.RunModelConversion(
            PineconeConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this.Name,
            "Get",
            () => this._mapper.MapFromStorageToDataModel(result, mapperOptions));
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetAsync(
        IEnumerable<TKey> keys,
        GetRecordOptions? options = default,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        if (options?.IncludeVectors is true && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

#pragma warning disable CA1851 // Bogus: Possible multiple enumerations of 'IEnumerable' collection
        var keysList = keys switch
        {
            IEnumerable<string> k => k.ToList(),
            IEnumerable<object> k => k.Cast<string>().ToList(),
            _ => throw new UnreachableException("string key should have been validated during model building")
        };
#pragma warning restore CA1851

        if (keysList.Count == 0)
        {
            yield break;
        }

        Sdk.FetchRequest request = new()
        {
            Namespace = this._options.IndexNamespace,
            Ids = keysList
        };

        var response = await this.RunIndexOperationAsync(
            "GetBatch",
            indexClient => indexClient.FetchAsync(request, cancellationToken: cancellationToken)).ConfigureAwait(false);
        if (response.Vectors is null || response.Vectors.Count == 0)
        {
            yield break;
        }

        StorageToDataModelMapperOptions mapperOptions = new() { IncludeVectors = options?.IncludeVectors is true };
        var records = VectorStoreErrorHandler.RunModelConversion(
            PineconeConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this.Name,
            "GetBatch",
            () => response.Vectors.Values.Select(x => this._mapper.MapFromStorageToDataModel(x, mapperOptions)));

        foreach (var record in records)
        {
            yield return record;
        }
    }

    /// <inheritdoc />
    public Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        Sdk.DeleteRequest request = new()
        {
            Namespace = this._options.IndexNamespace,
            Ids = [this.GetStringKey(key)]
        };

        return this.RunIndexOperationAsync(
            "Delete",
            indexClient => indexClient.DeleteAsync(request, cancellationToken: cancellationToken));
    }

    /// <inheritdoc />
    public Task DeleteAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        var keysList = keys switch
        {
            IEnumerable<string> k => k.ToList(),
            IEnumerable<object> k => k.Cast<string>().ToList(),
            _ => throw new UnreachableException("string key should have been validated during model building")
        };

        if (keysList.Count == 0)
        {
            return Task.CompletedTask;
        }

        Sdk.DeleteRequest request = new()
        {
            Namespace = this._options.IndexNamespace,
            Ids = keysList
        };

        return this.RunIndexOperationAsync(
            "DeleteBatch",
            indexClient => indexClient.DeleteAsync(request, cancellationToken: cancellationToken));
    }

    /// <inheritdoc />
    public async Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        // If an embedding generator is defined, invoke it once for all records.
        Embedding<float>? generatedEmbedding = null;

        Debug.Assert(this._model.VectorProperties.Count <= 1);
        if (this._model.VectorProperties is [{ EmbeddingGenerator: not null } vectorProperty])
        {
            if (vectorProperty.TryGenerateEmbedding<TRecord, Embedding<float>, ReadOnlyMemory<float>>(record, cancellationToken, out var task))
            {
                generatedEmbedding = await task.ConfigureAwait(false);
            }
            else
            {
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{vectorProperty.ModelName}' cannot produce an embedding of type '{typeof(Embedding<float>).Name}' for the given input type.");
            }
        }

        var vector = VectorStoreErrorHandler.RunModelConversion(
            PineconeConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this.Name,
            "Upsert",
            () => this._mapper.MapFromDataToStorageModel(record, generatedEmbedding));

        Sdk.UpsertRequest request = new()
        {
            Namespace = this._options.IndexNamespace,
            Vectors = [vector],
        };

        await this.RunIndexOperationAsync(
            "Upsert",
            indexClient => indexClient.UpsertAsync(request, cancellationToken: cancellationToken)).ConfigureAwait(false);

        return (TKey)(object)vector.Id;
    }

    /// <inheritdoc />
    public async Task<IReadOnlyList<TKey>> UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        // If an embedding generator is defined, invoke it once for all records.
        GeneratedEmbeddings<Embedding<float>>? generatedEmbeddings = null;

        if (this._model.VectorProperties is [{ EmbeddingGenerator: not null } vectorProperty])
        {
            var recordsList = records is IReadOnlyList<TRecord> r ? r : records.ToList();

            if (recordsList.Count == 0)
            {
                return [];
            }

            records = recordsList;

            if (vectorProperty.TryGenerateEmbeddings<TRecord, Embedding<float>, ReadOnlyMemory<float>>(records, cancellationToken, out var task))
            {
                generatedEmbeddings = await task.ConfigureAwait(false);

                Debug.Assert(generatedEmbeddings.Count == recordsList.Count);
            }
            else
            {
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{vectorProperty.ModelName}' cannot produce an embedding of type '{typeof(Embedding<float>).Name}' for the given input type.");
            }
        }

        var vectors = VectorStoreErrorHandler.RunModelConversion(
            PineconeConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this.Name,
            "UpsertBatch",
            () => records.Select((r, i) => this._mapper.MapFromDataToStorageModel(r, generatedEmbeddings?[i])).ToList());

        if (vectors.Count == 0)
        {
            return [];
        }

        Sdk.UpsertRequest request = new()
        {
            Namespace = this._options.IndexNamespace,
            Vectors = vectors,
        };

        await this.RunIndexOperationAsync(
            "UpsertBatch",
            indexClient => indexClient.UpsertAsync(request, cancellationToken: cancellationToken)).ConfigureAwait(false);

        return vectors.Select(x => (TKey)(object)x.Id).ToList();
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

            case null:
                throw new InvalidOperationException(VectorDataStrings.NoEmbeddingGeneratorWasConfiguredForSearch);

            default:
                throw new InvalidOperationException(
                    PineconeVectorStoreRecordFieldMapping.s_supportedVectorTypes.Contains(typeof(TInput))
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

    private async IAsyncEnumerable<VectorSearchResult<TRecord>> SearchCoreAsync<TVector>(
        TVector vector,
        int top,
        VectorStoreRecordVectorPropertyModel vectorProperty,
        string operationName,
        VectorSearchOptions<TRecord> options,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
        where TVector : notnull
    {
        Verify.NotNull(vector);
        Verify.NotLessThan(top, 1);

        if (vector is not ReadOnlyMemory<float> floatVector)
        {
            throw new NotSupportedException($"The provided vector type {vector.GetType().FullName} is not supported by the Pinecone connector." +
                $"Supported types are: {typeof(ReadOnlyMemory<float>).FullName}");
        }

        if (options.IncludeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        var filter = options switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => PineconeVectorStoreCollectionSearchMapping.BuildSearchFilter(options.OldFilter?.FilterClauses, this._model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new PineconeFilterTranslator().Translate(newFilter, this._model),
            _ => null
        };
#pragma warning restore CS0618

        Sdk.QueryRequest request = new()
        {
            TopK = (uint)(top + options.Skip),
            Namespace = this._options.IndexNamespace,
            IncludeValues = options.IncludeVectors,
            IncludeMetadata = true,
            Vector = floatVector,
            Filter = filter,
        };

        Sdk.QueryResponse response = await this.RunIndexOperationAsync(
            "VectorizedSearch",
            indexClient => indexClient.QueryAsync(request, cancellationToken: cancellationToken)).ConfigureAwait(false);

        if (response.Matches is null)
        {
            yield break;
        }

        // Pinecone does not provide a way to skip results, so we need to do it manually.
        var skippedResults = response.Matches
            .Skip(options.Skip);

        StorageToDataModelMapperOptions mapperOptions = new() { IncludeVectors = options.IncludeVectors is true };
        var records = VectorStoreErrorHandler.RunModelConversion(
            PineconeConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this.Name,
            "VectorizedSearch",
            () => skippedResults.Select(x => new VectorSearchResult<TRecord>(this._mapper.MapFromStorageToDataModel(new Sdk.Vector()
            {
                Id = x.Id,
                Values = x.Values ?? Array.Empty<float>(),
                Metadata = x.Metadata,
                SparseValues = x.SparseValues
            }, mapperOptions), x.Score)));

        foreach (var record in records)
        {
            yield return record;
        }
    }

    /// <inheritdoc />
    [Obsolete("Use either SearchEmbeddingAsync to search directly on embeddings, or SearchAsync to handle embedding generation internally as part of the call.")]
    public IAsyncEnumerable<VectorSearchResult<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, int top, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
        where TVector : notnull
        => this.SearchEmbeddingAsync(vector, top, options, cancellationToken);

    #endregion Search

    /// <inheritdoc/>
    public async IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top, GetFilteredRecordOptions<TRecord>? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(filter);
        Verify.NotLessThan(top, 1);

        if (options?.OrderBy.Values.Count > 0)
        {
            throw new NotSupportedException("Pinecone does not support ordering.");
        }

        options ??= new();

        if (options.IncludeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        Sdk.QueryRequest request = new()
        {
            TopK = (uint)(top + options.Skip),
            Namespace = this._options.IndexNamespace,
            IncludeValues = options.IncludeVectors,
            IncludeMetadata = true,
            // "Either 'vector' or 'ID' must be provided"
            // Since we are doing a query, we don't have a vector to provide, so we fake one.
            // When https://github.com/pinecone-io/pinecone-dotnet-client/issues/43 gets implemented, we need to switch.
            Vector = new ReadOnlyMemory<float>(new float[this._model.VectorProperty.Dimensions]),
            Filter = new PineconeFilterTranslator().Translate(filter, this._model),
        };

        Sdk.QueryResponse response = await this.RunIndexOperationAsync(
            "Get",
            indexClient => indexClient.QueryAsync(request, cancellationToken: cancellationToken)).ConfigureAwait(false);

        if (response.Matches is null)
        {
            yield break;
        }

        StorageToDataModelMapperOptions mapperOptions = new() { IncludeVectors = options.IncludeVectors is true };
        var records = VectorStoreErrorHandler.RunModelConversion(
            PineconeConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this.Name,
            "Query",
            () => response.Matches.Skip(options.Skip).Select(x => this._mapper.MapFromStorageToDataModel(new Sdk.Vector()
            {
                Id = x.Id,
                Values = x.Values ?? Array.Empty<float>(),
                Metadata = x.Metadata,
                SparseValues = x.SparseValues
            }, mapperOptions)));

        foreach (var record in records)
        {
            yield return record;
        }
    }

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreRecordCollectionMetadata) ? this._collectionMetadata :
            serviceType == typeof(Sdk.PineconeClient) ? this._pineconeClient :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }

    private async Task<T> RunIndexOperationAsync<T>(string operationName, Func<IndexClient, Task<T>> operation)
    {
        try
        {
            if (this._indexClient is null)
            {
                // If we don't provide "host" to the Index method, it's going to perform
                // a blocking call to DescribeIndexAsync!!
                string hostName = (await this._pineconeClient.DescribeIndexAsync(this.Name).ConfigureAwait(false)).Host;
                this._indexClient = this._pineconeClient.Index(host: hostName);
            }

            return await operation.Invoke(this._indexClient).ConfigureAwait(false);
        }
        catch (PineconeApiException ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = PineconeConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = operationName
            };
        }
    }

    private async Task<T> RunCollectionOperationAsync<T>(string operationName, Func<Task<T>> operation)
    {
        try
        {
            return await operation.Invoke().ConfigureAwait(false);
        }
        catch (PineconeApiException ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = PineconeConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = operationName
            };
        }
    }

    private static ServerlessSpecCloud MapCloud(string serverlessIndexCloud)
        => serverlessIndexCloud switch
        {
            "aws" => ServerlessSpecCloud.Aws,
            "azure" => ServerlessSpecCloud.Azure,
            "gcp" => ServerlessSpecCloud.Gcp,
            _ => throw new ArgumentException($"Invalid serverless index cloud: {serverlessIndexCloud}.", nameof(serverlessIndexCloud))
        };

    private static CreateIndexRequestMetric MapDistanceFunction(VectorStoreRecordVectorPropertyModel vectorProperty)
        => vectorProperty.DistanceFunction switch
        {
            DistanceFunction.CosineSimilarity or null => CreateIndexRequestMetric.Cosine,
            DistanceFunction.DotProductSimilarity => CreateIndexRequestMetric.Dotproduct,
            DistanceFunction.EuclideanSquaredDistance => CreateIndexRequestMetric.Euclidean,
            _ => throw new NotSupportedException($"Distance function '{vectorProperty.DistanceFunction}' is not supported.")
        };

    private static void VerifyCollectionName(string collectionName)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        // Based on https://docs.pinecone.io/troubleshooting/restrictions-on-index-names
        foreach (char character in collectionName)
        {
            if (!((character is >= 'a' and <= 'z') || character is '-' || (character is >= '0' and <= '9')))
            {
                throw new ArgumentException("Collection name must contain only ASCII lowercase letters, digits and dashes.", nameof(collectionName));
            }
        }
    }

    private string GetStringKey(TKey key)
    {
        Verify.NotNull(key);

        var stringKey = key as string ?? throw new UnreachableException("string key should have been validated during model building");

        Verify.NotNullOrWhiteSpace(stringKey, nameof(key));

        return stringKey;
    }
}
