// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Pinecone;
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

    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    private readonly Sdk.PineconeClient _pineconeClient;
    private readonly PineconeVectorStoreRecordCollectionOptions<TRecord> _options;
    private readonly VectorStoreRecordPropertyReader _propertyReader;
    private readonly IVectorStoreRecordMapper<TRecord, Sdk.Vector> _mapper;
    private IndexClient? _indexClient;

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
        VerifyCollectionName(collectionName);

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
    public virtual Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
        => this.RunCollectionOperationAsync(
            "CollectionExists",
            async () =>
            {
                var collections = await this._pineconeClient.ListIndexesAsync(cancellationToken: cancellationToken).ConfigureAwait(false);

                return collections.Indexes?.Any(x => x.Name == this.CollectionName) is true;
            });

    /// <inheritdoc />
    public virtual Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        // we already run through record property validation, so a single VectorStoreRecordVectorProperty is guaranteed.
        var vectorProperty = this._propertyReader.VectorProperty!;

        if (!string.IsNullOrEmpty(vectorProperty.IndexKind) && vectorProperty.IndexKind != "PGA")
        {
            throw new InvalidOperationException(
                $"IndexKind of '{vectorProperty.IndexKind}' for property '{vectorProperty.DataModelPropertyName}' is not supported. Pinecone only supports 'PGA' (Pinecone Graph Algorithm), which is always enabled.");
        }

        CreateIndexRequest request = new()
        {
            Name = this.CollectionName,
            Dimension = vectorProperty.Dimensions ?? throw new InvalidOperationException($"Property {nameof(vectorProperty.Dimensions)} on {nameof(VectorStoreRecordVectorProperty)} '{vectorProperty.DataModelPropertyName}' must be set to a positive integer to create a collection."),
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
    public virtual async Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
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
    public virtual async Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            await this._pineconeClient.DeleteIndexAsync(this.CollectionName, cancellationToken: cancellationToken).ConfigureAwait(false);
        }
        catch (NotFoundError)
        {
            // If the collection does not exist, we should ignore the exception.
        }
        catch (PineconeApiException other)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", other)
            {
                VectorStoreType = DatabaseName,
                CollectionName = this.CollectionName,
                OperationName = "DeleteCollection"
            };
        }
    }

    /// <inheritdoc />
    public virtual async Task<TRecord?> GetAsync(string key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        Sdk.FetchRequest request = new()
        {
            Namespace = this._options.IndexNamespace,
            Ids = [key]
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
            DatabaseName,
            this.CollectionName,
            "Get",
            () => this._mapper.MapFromStorageToDataModel(result, mapperOptions));
    }

    /// <inheritdoc />
    public virtual async IAsyncEnumerable<TRecord> GetBatchAsync(
        IEnumerable<string> keys,
        GetRecordOptions? options = default,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        List<string> keysList = keys.ToList();
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
            DatabaseName,
            this.CollectionName,
            "GetBatch",
            () => response.Vectors.Values.Select(x => this._mapper.MapFromStorageToDataModel(x, mapperOptions)));

        foreach (var record in records)
        {
            yield return record;
        }
    }

    /// <inheritdoc />
    public virtual Task DeleteAsync(string key, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(key);

        Sdk.DeleteRequest request = new()
        {
            Namespace = this._options.IndexNamespace,
            Ids = [key]
        };

        return this.RunIndexOperationAsync(
            "Delete",
            indexClient => indexClient.DeleteAsync(request, cancellationToken: cancellationToken));
    }

    /// <inheritdoc />
    public virtual Task DeleteBatchAsync(IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        List<string> keysList = keys.ToList();
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
    public virtual async Task<string> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        var vector = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this.CollectionName,
            "Upsert",
            () => this._mapper.MapFromDataToStorageModel(record));

        Sdk.UpsertRequest request = new()
        {
            Namespace = this._options.IndexNamespace,
            Vectors = [vector],
        };

        await this.RunIndexOperationAsync(
            "Upsert",
            indexClient => indexClient.UpsertAsync(request, cancellationToken: cancellationToken)).ConfigureAwait(false);

        return vector.Id;
    }

    /// <inheritdoc />
    public virtual async IAsyncEnumerable<string> UpsertBatchAsync(IEnumerable<TRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        var vectors = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this.CollectionName,
            "UpsertBatch",
            () => records.Select(this._mapper.MapFromDataToStorageModel).ToList());

        if (vectors.Count == 0)
        {
            yield break;
        }

        Sdk.UpsertRequest request = new()
        {
            Namespace = this._options.IndexNamespace,
            Vectors = vectors,
        };

        await this.RunIndexOperationAsync(
            "UpsertBatch",
            indexClient => indexClient.UpsertAsync(request, cancellationToken: cancellationToken)).ConfigureAwait(false);

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

        options ??= s_defaultVectorSearchOptions;

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        var filter = options switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => PineconeVectorStoreCollectionSearchMapping.BuildSearchFilter(options.OldFilter?.FilterClauses, this._propertyReader.StoragePropertyNamesMap),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new PineconeFilterTranslator().Translate(newFilter, this._propertyReader.StoragePropertyNamesMap),
            _ => null
        };
#pragma warning restore CS0618

        Sdk.QueryRequest request = new()
        {
            TopK = (uint)(options.Top + options.Skip),
            Namespace = this._options.IndexNamespace,
            IncludeValues = options.IncludeVectors,
            IncludeMetadata = true,
            Vector = floatVector,
            Filter = filter,
        };

        Sdk.QueryResponse response = await this.RunIndexOperationAsync(
            "Query",
            indexClient => indexClient.QueryAsync(request, cancellationToken: cancellationToken)).ConfigureAwait(false);

        if (response.Matches is null)
        {
            return new VectorSearchResults<TRecord>(Array.Empty<VectorSearchResult<TRecord>>().ToAsyncEnumerable());
        }

        // Pinecone does not provide a way to skip results, so we need to do it manually.
        var skippedResults = response.Matches
            .Skip(options.Skip);

        StorageToDataModelMapperOptions mapperOptions = new() { IncludeVectors = options.IncludeVectors is true };
        var records = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this.CollectionName,
            "Query",
            () => skippedResults.Select(x => new VectorSearchResult<TRecord>(this._mapper.MapFromStorageToDataModel(new Sdk.Vector()
            {
                Id = x.Id,
                Values = x.Values ?? Array.Empty<float>(),
                Metadata = x.Metadata,
                SparseValues = x.SparseValues
            }, mapperOptions), x.Score)))
            .ToAsyncEnumerable();

        return new(records);
    }

    private async Task<T> RunIndexOperationAsync<T>(string operationName, Func<IndexClient, Task<T>> operation)
    {
        try
        {
            if (this._indexClient is null)
            {
                // If we don't provide "host" to the Index method, it's going to perform
                // a blocking call to DescribeIndexAsync!!
                string hostName = (await this._pineconeClient.DescribeIndexAsync(this.CollectionName).ConfigureAwait(false)).Host;
                this._indexClient = this._pineconeClient.Index(host: hostName);
            }

            return await operation.Invoke(this._indexClient).ConfigureAwait(false);
        }
        catch (PineconeApiException ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreType = DatabaseName,
                CollectionName = this.CollectionName,
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
                VectorStoreType = DatabaseName,
                CollectionName = this.CollectionName,
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

    private static CreateIndexRequestMetric MapDistanceFunction(VectorStoreRecordVectorProperty vectorProperty)
        => vectorProperty.DistanceFunction switch
        {
            DistanceFunction.CosineSimilarity => CreateIndexRequestMetric.Cosine,
            DistanceFunction.DotProductSimilarity => CreateIndexRequestMetric.Dotproduct,
            DistanceFunction.EuclideanSquaredDistance => CreateIndexRequestMetric.Euclidean,
            null => CreateIndexRequestMetric.Cosine,
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
}
