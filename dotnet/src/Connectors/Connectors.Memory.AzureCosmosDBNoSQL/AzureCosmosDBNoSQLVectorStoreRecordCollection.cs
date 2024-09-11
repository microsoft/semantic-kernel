﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.SemanticKernel.Data;
using DistanceFunction = Microsoft.Azure.Cosmos.DistanceFunction;
using IndexKind = Microsoft.SemanticKernel.Data.IndexKind;
using SKDistanceFunction = Microsoft.SemanticKernel.Data.DistanceFunction;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

/// <summary>
/// Service for storing and retrieving vector records, that uses Azure CosmosDB NoSQL as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class AzureCosmosDBNoSQLVectorStoreRecordCollection<TRecord> :
    IVectorStoreRecordCollection<string, TRecord>,
    IVectorStoreRecordCollection<AzureCosmosDBNoSQLCompositeKey, TRecord>
    where TRecord : class
#pragma warning restore CA1711 // Identifiers should not have incorrect
{
    /// <summary>The name of this database for telemetry purposes.</summary>
    private const string DatabaseName = "AzureCosmosDBNoSQL";

    /// <summary>A set of types that a key on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedKeyTypes =
    [
        typeof(string)
    ];

    /// <summary>A set of types that data properties on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedDataTypes =
    [
        typeof(string),
        typeof(int),
        typeof(long),
        typeof(double),
        typeof(float),
        typeof(bool),
        typeof(DateTimeOffset),
        typeof(int?),
        typeof(long?),
        typeof(double?),
        typeof(float?),
        typeof(bool?),
        typeof(DateTimeOffset?),
    ];

    /// <summary>A set of types that vector properties on the provided model may have, based on <see cref="VectorDataType"/> enumeration.</summary>
    private static readonly HashSet<Type> s_supportedVectorTypes =
    [
        // Float16
#if NET5_0_OR_GREATER
        typeof(ReadOnlyMemory<Half>),
        typeof(ReadOnlyMemory<Half>?),
#endif
        // Float32
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?),
        // Uint8
        typeof(ReadOnlyMemory<byte>),
        typeof(ReadOnlyMemory<byte>?),
        // Int8
        typeof(ReadOnlyMemory<sbyte>),
        typeof(ReadOnlyMemory<sbyte>?),
    ];

    /// <summary><see cref="Database"/> that can be used to manage the collections in Azure CosmosDB NoSQL.</summary>
    private readonly Database _database;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly AzureCosmosDBNoSQLVectorStoreRecordCollectionOptions<TRecord> _options;

    /// <summary>A definition of the current storage model.</summary>
    private readonly VectorStoreRecordDefinition _vectorStoreRecordDefinition;

    /// <summary>The storage names of all non vector fields on the current model.</summary>
    private readonly List<string> _nonVectorStoragePropertyNames = [];

    /// <summary>A dictionary that maps from a property name to the storage name that should be used when serializing it to json for data and vector properties.</summary>
    private readonly Dictionary<string, string> _storagePropertyNames = [];

    /// <summary>The storage name of the key field for the collections that this class is used with.</summary>
    private readonly string _keyStoragePropertyName;

    /// <summary>The key property of the current storage model.</summary>
    private readonly VectorStoreRecordKeyProperty _keyProperty;

    /// <summary>The property name to use as partition key.</summary>
    private readonly string _partitionKeyPropertyName;

    /// <summary>The storage property name to use as partition key.</summary>
    private readonly string _partitionKeyStoragePropertyName;

    /// <summary>The mapper to use when mapping between the consumer data model and the Azure CosmosDB NoSQL record.</summary>
    private readonly IVectorStoreRecordMapper<TRecord, JsonObject> _mapper;

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
        // Verify.
        Verify.NotNull(database);
        Verify.NotNullOrWhiteSpace(collectionName);

        // Assign.
        this._database = database;
        this.CollectionName = collectionName;
        this._options = options ?? new();
        this._vectorStoreRecordDefinition = this._options.VectorStoreRecordDefinition ?? VectorStoreRecordPropertyReader.CreateVectorStoreRecordDefinitionFromType(typeof(TRecord), true);
        var jsonSerializerOptions = this._options.JsonSerializerOptions ?? JsonSerializerOptions.Default;

        // Validate property types.
        var properties = VectorStoreRecordPropertyReader.SplitDefinitionAndVerify(typeof(TRecord).Name, this._vectorStoreRecordDefinition, supportsMultipleVectors: true, requiresAtLeastOneVector: false);
        VectorStoreRecordPropertyReader.VerifyPropertyTypes([properties.KeyProperty], s_supportedKeyTypes, "Key");
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(properties.DataProperties, s_supportedDataTypes, "Data", supportEnumerable: true);
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(properties.VectorProperties, s_supportedVectorTypes, "Vector");

        // Get storage names and store for later use.
        this._keyProperty = properties.KeyProperty;
        this._storagePropertyNames = VectorStoreRecordPropertyReader.BuildPropertyNameToJsonPropertyNameMap(properties, typeof(TRecord), jsonSerializerOptions);

        // Assign mapper.
        this._mapper = this._options.JsonObjectCustomMapper ??
            new AzureCosmosDBNoSQLVectorStoreRecordMapper<TRecord>(
                this._storagePropertyNames[this._keyProperty.DataModelPropertyName],
                this._storagePropertyNames,
                jsonSerializerOptions);

        // Use Azure CosmosDB NoSQL reserved key property name as storage key property name.
        this._storagePropertyNames[this._keyProperty.DataModelPropertyName] = AzureCosmosDBNoSQLConstants.ReservedKeyPropertyName;
        this._keyStoragePropertyName = AzureCosmosDBNoSQLConstants.ReservedKeyPropertyName;

        // If partition key is not provided, use key property as a partition key.
        this._partitionKeyPropertyName = !string.IsNullOrWhiteSpace(this._options.PartitionKeyPropertyName) ?
            this._options.PartitionKeyPropertyName! :
            this._keyProperty.DataModelPropertyName;

        VerifyPartitionKeyProperty(this._partitionKeyPropertyName, this._vectorStoreRecordDefinition);

        this._partitionKeyStoragePropertyName = this._storagePropertyNames[this._partitionKeyPropertyName];

        this._nonVectorStoragePropertyNames = properties.DataProperties
            .Cast<VectorStoreRecordProperty>()
            .Concat([properties.KeyProperty])
            .Select(x => this._storagePropertyNames[x.DataModelPropertyName])
            .ToList();
    }

    /// <inheritdoc />
    public Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        return this.RunOperationAsync("GetContainerQueryIterator", async () =>
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
        });
    }

    /// <inheritdoc />
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        return this.RunOperationAsync("CreateContainer", () =>
            this._database.CreateContainerAsync(this.GetContainerProperties(), cancellationToken: cancellationToken));
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
    {
        return this.RunOperationAsync("DeleteContainer", () =>
            this._database
                .GetContainer(this.CollectionName)
                .DeleteContainerAsync(cancellationToken: cancellationToken));
    }

    #region Implementation of IVectorStoreRecordCollection<string, TRecord>

    /// <inheritdoc />
    public Task DeleteAsync(string key, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        // Use record key as partition key
        var compositeKey = new AzureCosmosDBNoSQLCompositeKey(recordKey: key, partitionKey: key);

        return this.InternalDeleteAsync([compositeKey], cancellationToken);
    }

    /// <inheritdoc />
    public Task DeleteBatchAsync(IEnumerable<string> keys, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        // Use record keys as partition keys
        var compositeKeys = keys.Select(key => new AzureCosmosDBNoSQLCompositeKey(recordKey: key, partitionKey: key));

        return this.InternalDeleteAsync(compositeKeys, cancellationToken);
    }

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(string key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        // Use record key as partition key
        var compositeKey = new AzureCosmosDBNoSQLCompositeKey(recordKey: key, partitionKey: key);

        return await this.InternalGetAsync([compositeKey], options, cancellationToken)
            .FirstOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetBatchAsync(
        IEnumerable<string> keys,
        GetRecordOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        // Use record keys as partition keys
        var compositeKeys = keys.Select(key => new AzureCosmosDBNoSQLCompositeKey(recordKey: key, partitionKey: key));

        await foreach (var record in this.InternalGetAsync(compositeKeys, options, cancellationToken).ConfigureAwait(false))
        {
            if (record is not null)
            {
                yield return record;
            }
        }
    }

    /// <inheritdoc />
    public async Task<string> UpsertAsync(TRecord record, UpsertRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        var key = await this.InternalUpsertAsync(record, cancellationToken).ConfigureAwait(false);

        return key.RecordKey;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> UpsertBatchAsync(
        IEnumerable<TRecord> records,
        UpsertRecordOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        var tasks = records.Select(record => this.InternalUpsertAsync(record, cancellationToken));

        var keys = await Task.WhenAll(tasks).ConfigureAwait(false);

        foreach (var key in keys)
        {
            if (key is not null)
            {
                yield return key.RecordKey;
            }
        }
    }

    #endregion

    #region Implementation of IVectorStoreRecordCollection<AzureCosmosDBNoSQLCompositeKey, TRecord>

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(AzureCosmosDBNoSQLCompositeKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        return await this.InternalGetAsync([key], options, cancellationToken)
            .FirstOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetBatchAsync(
        IEnumerable<AzureCosmosDBNoSQLCompositeKey> keys,
        GetRecordOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var record in this.InternalGetAsync(keys, options, cancellationToken).ConfigureAwait(false))
        {
            if (record is not null)
            {
                yield return record;
            }
        }
    }

    /// <inheritdoc />
    public Task DeleteAsync(AzureCosmosDBNoSQLCompositeKey key, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        return this.InternalDeleteAsync([key], cancellationToken);
    }

    /// <inheritdoc />
    public Task DeleteBatchAsync(IEnumerable<AzureCosmosDBNoSQLCompositeKey> keys, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        return this.InternalDeleteAsync(keys, cancellationToken);
    }

    /// <inheritdoc />
    Task<AzureCosmosDBNoSQLCompositeKey> IVectorStoreRecordCollection<AzureCosmosDBNoSQLCompositeKey, TRecord>.UpsertAsync(TRecord record, UpsertRecordOptions? options, CancellationToken cancellationToken)
    {
        return this.InternalUpsertAsync(record, cancellationToken);
    }

    /// <inheritdoc />
    async IAsyncEnumerable<AzureCosmosDBNoSQLCompositeKey> IVectorStoreRecordCollection<AzureCosmosDBNoSQLCompositeKey, TRecord>.UpsertBatchAsync(
        IEnumerable<TRecord> records,
        UpsertRecordOptions? options,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        Verify.NotNull(records);

        var tasks = records.Select(record => this.InternalUpsertAsync(record, cancellationToken));

        var keys = await Task.WhenAll(tasks).ConfigureAwait(false);

        foreach (var key in keys)
        {
            if (key is not null)
            {
                yield return key;
            }
        }
    }

    #endregion

    #region private

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

    private static void VerifyPartitionKeyProperty(string partitionKeyPropertyName, VectorStoreRecordDefinition definition)
    {
        var partitionKeyProperty = definition.Properties
            .FirstOrDefault(l => l.DataModelPropertyName.Equals(partitionKeyPropertyName, StringComparison.Ordinal));

        if (partitionKeyProperty is null)
        {
            throw new ArgumentException("Partition key property must be part of record definition.");
        }

        if (partitionKeyProperty.PropertyType != typeof(string))
        {
            throw new ArgumentException("Partition key property must be string.");
        }
    }

    /// <summary>
    /// Returns instance of <see cref="ContainerProperties"/> with applied indexing policy.
    /// More information here: <see href="https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/how-to-manage-indexing-policy"/>.
    /// </summary>
    private ContainerProperties GetContainerProperties()
    {
        // Process Vector properties.
        var embeddings = new Collection<Embedding>();
        var vectorIndexPaths = new Collection<VectorIndexPath>();

        foreach (var property in this._vectorStoreRecordDefinition.Properties.OfType<VectorStoreRecordVectorProperty>())
        {
            var vectorPropertyName = this._storagePropertyNames[property.DataModelPropertyName];

            if (property.Dimensions is not > 0)
            {
                throw new VectorStoreOperationException($"Property {nameof(property.Dimensions)} on {nameof(VectorStoreRecordVectorProperty)} '{property.DataModelPropertyName}' must be set to a positive integer to create a collection.");
            }

            var path = $"/{vectorPropertyName}";

            var embedding = new Embedding
            {
                DataType = GetDataType(property.PropertyType, vectorPropertyName),
                Dimensions = (ulong)property.Dimensions,
                DistanceFunction = GetDistanceFunction(property.DistanceFunction, vectorPropertyName),
                Path = path
            };

            var vectorIndexPath = new VectorIndexPath
            {
                Type = GetIndexKind(property.IndexKind, vectorPropertyName),
                Path = path
            };

            embeddings.Add(embedding);
            vectorIndexPaths.Add(vectorIndexPath);
        }

        var vectorEmbeddingPolicy = new VectorEmbeddingPolicy(embeddings);
        var indexingPolicy = new IndexingPolicy
        {
            VectorIndexes = vectorIndexPaths,
            IndexingMode = this._options.IndexingMode,
            Automatic = this._options.Automatic
        };

        if (indexingPolicy.IndexingMode != IndexingMode.None)
        {
            // Process Data properties.
            foreach (var property in this._vectorStoreRecordDefinition.Properties.OfType<VectorStoreRecordDataProperty>())
            {
                if (property.IsFilterable || property.IsFullTextSearchable)
                {
                    indexingPolicy.IncludedPaths.Add(new IncludedPath { Path = $"/{this._storagePropertyNames[property.DataModelPropertyName]}/?" });
                }
            }

            // Adding special mandatory indexing path.
            indexingPolicy.IncludedPaths.Add(new IncludedPath { Path = "/" });

            // Exclude vector paths to ensure optimized performance.
            foreach (var vectorIndexPath in vectorIndexPaths)
            {
                indexingPolicy.ExcludedPaths.Add(new ExcludedPath { Path = $"{vectorIndexPath.Path}/*" });
            }
        }

        return new ContainerProperties(this.CollectionName, partitionKeyPath: $"/{this._partitionKeyStoragePropertyName}")
        {
            VectorEmbeddingPolicy = vectorEmbeddingPolicy,
            IndexingPolicy = indexingPolicy
        };
    }

    /// <summary>
    /// More information about Azure CosmosDB NoSQL index kinds here: <see href="https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/vector-search#vector-indexing-policies" />.
    /// </summary>
    private static VectorIndexType GetIndexKind(string? indexKind, string vectorPropertyName)
    {
        return indexKind switch
        {
            IndexKind.Flat => VectorIndexType.Flat,
            IndexKind.QuantizedFlat => VectorIndexType.QuantizedFlat,
            IndexKind.DiskAnn => VectorIndexType.DiskANN,
            _ => throw new InvalidOperationException($"Index kind '{indexKind}' on {nameof(VectorStoreRecordVectorProperty)} '{vectorPropertyName}' is not supported by the Azure CosmosDB NoSQL VectorStore.")
        };
    }

    /// <summary>
    /// More information about Azure CosmosDB NoSQL distance functions here: <see href="https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/vector-search#container-vector-policies" />.
    /// </summary>
    private static DistanceFunction GetDistanceFunction(string? distanceFunction, string vectorPropertyName)
    {
        return distanceFunction switch
        {
            SKDistanceFunction.CosineSimilarity => DistanceFunction.Cosine,
            SKDistanceFunction.DotProductSimilarity => DistanceFunction.DotProduct,
            SKDistanceFunction.EuclideanDistance => DistanceFunction.Euclidean,
            _ => throw new InvalidOperationException($"Distance function '{distanceFunction}' for {nameof(VectorStoreRecordVectorProperty)} '{vectorPropertyName}' is not supported by the Azure CosmosDB NoSQL VectorStore.")
        };
    }

    /// <summary>
    /// Returns <see cref="VectorDataType"/> based on vector property type.
    /// </summary>
    private static VectorDataType GetDataType(Type vectorDataType, string vectorPropertyName)
    {
        return vectorDataType switch
        {
#if NET5_0_OR_GREATER
            Type type when type == typeof(ReadOnlyMemory<Half>) || type == typeof(ReadOnlyMemory<Half>?) => VectorDataType.Float16,
#endif
            Type type when type == typeof(ReadOnlyMemory<float>) || type == typeof(ReadOnlyMemory<float>?) => VectorDataType.Float32,
            Type type when type == typeof(ReadOnlyMemory<byte>) || type == typeof(ReadOnlyMemory<byte>?) => VectorDataType.Uint8,
            Type type when type == typeof(ReadOnlyMemory<sbyte>) || type == typeof(ReadOnlyMemory<sbyte>?) => VectorDataType.Int8,
            _ => throw new InvalidOperationException($"Data type '{vectorDataType}' for {nameof(VectorStoreRecordVectorProperty)} '{vectorPropertyName}' is not supported by the Azure CosmosDB NoSQL VectorStore.")
        };
    }

    private async IAsyncEnumerable<TRecord> InternalGetAsync(
        IEnumerable<AzureCosmosDBNoSQLCompositeKey> keys,
        GetRecordOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        const string OperationName = "GetItemQueryIterator";

        var includeVectors = options?.IncludeVectors ?? false;
        var fields = new List<string>(includeVectors ? this._storagePropertyNames.Values : this._nonVectorStoragePropertyNames);
        var queryDefinition = this.GetSelectQuery(keys.ToList(), fields);

        await foreach (var jsonObject in this.GetItemsAsync(queryDefinition, cancellationToken).ConfigureAwait(false))
        {
            yield return VectorStoreErrorHandler.RunModelConversion(
                DatabaseName,
                this.CollectionName,
                OperationName,
                () => this._mapper.MapFromStorageToDataModel(jsonObject, new() { IncludeVectors = includeVectors }));
        }
    }

    private async Task<AzureCosmosDBNoSQLCompositeKey> InternalUpsertAsync(
        TRecord record,
        CancellationToken cancellationToken)
    {
        Verify.NotNull(record);

        const string OperationName = "UpsertItem";

        var jsonObject = VectorStoreErrorHandler.RunModelConversion(
                DatabaseName,
                this.CollectionName,
                OperationName,
                () => this._mapper.MapFromDataToStorageModel(record));

        var keyValue = jsonObject.TryGetPropertyValue(this._keyStoragePropertyName, out var jsonKey) ? jsonKey?.ToString() : null;
        var partitionKeyValue = jsonObject.TryGetPropertyValue(this._partitionKeyStoragePropertyName, out var jsonPartitionKey) ? jsonPartitionKey?.ToString() : null;

        if (string.IsNullOrWhiteSpace(keyValue))
        {
            throw new VectorStoreOperationException($"Key property {this._keyProperty.DataModelPropertyName} is not initialized.");
        }

        if (string.IsNullOrWhiteSpace(partitionKeyValue))
        {
            throw new VectorStoreOperationException($"Partition key property {this._partitionKeyPropertyName} is not initialized.");
        }

        await this.RunOperationAsync(OperationName, () =>
            this._database
                .GetContainer(this.CollectionName)
                .UpsertItemAsync(jsonObject, new PartitionKey(partitionKeyValue), cancellationToken: cancellationToken))
            .ConfigureAwait(false);

        return new AzureCosmosDBNoSQLCompositeKey(keyValue!, partitionKeyValue!);
    }

    private async Task InternalDeleteAsync(IEnumerable<AzureCosmosDBNoSQLCompositeKey> keys, CancellationToken cancellationToken)
    {
        Verify.NotNull(keys);

        var tasks = keys.Select(key =>
        {
            Verify.NotNullOrWhiteSpace(key.RecordKey);
            Verify.NotNullOrWhiteSpace(key.PartitionKey);

            return this.RunOperationAsync("DeleteItem", () =>
                this._database
                    .GetContainer(this.CollectionName)
                    .DeleteItemAsync<JsonObject>(key.RecordKey, new PartitionKey(key.PartitionKey), cancellationToken: cancellationToken));
        });

        await Task.WhenAll(tasks).ConfigureAwait(false);
    }

    private QueryDefinition GetSelectQuery(List<AzureCosmosDBNoSQLCompositeKey> keys, List<string> fields)
    {
        Verify.True(keys.Count > 0, "At least one key should be provided.", nameof(keys));

        const string WhereClauseDelimiter = " OR ";
        const string SelectClauseDelimiter = ",";

        const string RecordKeyVariableName = "rk";
        const string PartitionKeyVariableName = "pk";

        const string TableVariableName = "x";

        var selectClauseArguments = string.Join(SelectClauseDelimiter,
            fields.Select(field => $"{TableVariableName}.{field}"));

        var whereClauseArguments = string.Join(WhereClauseDelimiter,
            keys.Select((key, index) =>
                $"({TableVariableName}.{this._keyStoragePropertyName} = @{RecordKeyVariableName}{index} AND " +
                $"{TableVariableName}.{this._partitionKeyStoragePropertyName} = @{PartitionKeyVariableName}{index})"));

        var query = $"SELECT {selectClauseArguments} FROM {TableVariableName} WHERE {whereClauseArguments}";

        var queryDefinition = new QueryDefinition(query);

        for (var i = 0; i < keys.Count; i++)
        {
            var recordKey = keys[i].RecordKey;
            var partitionKey = keys[i].PartitionKey;

            Verify.NotNullOrWhiteSpace(recordKey);
            Verify.NotNullOrWhiteSpace(partitionKey);

            queryDefinition.WithParameter($"@{RecordKeyVariableName}{i}", recordKey);
            queryDefinition.WithParameter($"@{PartitionKeyVariableName}{i}", partitionKey);
        }

        return queryDefinition;
    }

    private async IAsyncEnumerable<JsonObject> GetItemsAsync(QueryDefinition queryDefinition, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        var iterator = this._database
            .GetContainer(this.CollectionName)
            .GetItemQueryIterator<JsonObject>(queryDefinition);

        while (iterator.HasMoreResults)
        {
            var response = await iterator.ReadNextAsync(cancellationToken).ConfigureAwait(false);

            foreach (var record in response.Resource)
            {
                if (record is not null)
                {
                    yield return record;
                }
            }
        }
    }

    #endregion
}
