// Copyright (c) Microsoft. All rights reserved.

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
public sealed class AzureCosmosDBNoSQLVectorStoreRecordCollection<TRecord> : IVectorStoreRecordCollection<string, TRecord> where TRecord : class
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
        var partitionKeyPropertyName = !string.IsNullOrWhiteSpace(this._options.PartitionKeyPropertyName) ?
            this._options.PartitionKeyPropertyName! :
            this._keyProperty.DataModelPropertyName;

        this._partitionKeyStoragePropertyName = this._storagePropertyNames[partitionKeyPropertyName];

        this._nonVectorStoragePropertyNames = properties.DataProperties
            .Cast<VectorStoreRecordProperty>()
            .Concat([properties.KeyProperty])
            .Select(x => this._storagePropertyNames[x.DataModelPropertyName])
            .ToList();
    }

    /// <inheritdoc />
    public Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        return this.RunOperationAsync("CollectionExists", async () =>
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
    public Task DeleteAsync(string key, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(key);

        return this.DeleteItemsAsync([key], cancellationToken);
    }

    /// <inheritdoc />
    public Task DeleteBatchAsync(IEnumerable<string> keys, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        return this.DeleteItemsAsync(keys, cancellationToken);
    }

    /// <inheritdoc />
    public Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        return this.RunOperationAsync("DeleteContainer", () =>
            this._database
                .GetContainer(this.CollectionName)
                .DeleteContainerAsync(cancellationToken: cancellationToken));
    }

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(string key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        return await this.GetBatchAsync([key], options, cancellationToken)
            .FirstOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetBatchAsync(
        IEnumerable<string> keys,
        GetRecordOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        const string OperationName = "GetItems";

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

    /// <inheritdoc />
    public async Task<string> UpsertAsync(TRecord record, UpsertRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        const string OperationName = "UpsertItem";

        var jsonObject = VectorStoreErrorHandler.RunModelConversion(
                DatabaseName,
                this.CollectionName,
                OperationName,
                () => this._mapper.MapFromDataToStorageModel(record));

        var jsonObjectKey = jsonObject.TryGetPropertyValue(this._keyStoragePropertyName, out var jsonKey) ? jsonKey?.ToString() : null;
        var jsonObjectPartitionKeyValue = jsonObject.TryGetPropertyValue(this._partitionKeyStoragePropertyName, out var jsonPartitionKey) ? jsonPartitionKey?.ToString() : null;

        return await this.RunOperationAsync(OperationName, () =>
            this.UpsertItemAsync(jsonObjectKey, jsonObjectPartitionKeyValue, jsonObject, cancellationToken)).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> UpsertBatchAsync(
        IEnumerable<TRecord> records,
        UpsertRecordOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        var tasks = records.Select(record => this.UpsertAsync(record, options, cancellationToken));

        var keys = await Task.WhenAll(tasks).ConfigureAwait(false);

        foreach (var key in keys)
        {
            if (!string.IsNullOrWhiteSpace(key))
            {
                yield return key;
            }
        }
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

    private async Task RunOperationAsync(string operationName, Func<Task> operation)
    {
        try
        {
            await operation.Invoke().ConfigureAwait(false);
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

    private ContainerProperties GetContainerProperties()
    {
        var embeddings = new Collection<Embedding>();
        var vectorIndexes = new Collection<VectorIndexPath>();

        foreach (var property in this._vectorStoreRecordDefinition.Properties.OfType<VectorStoreRecordVectorProperty>())
        {
            var vectorPropertyName = this._storagePropertyNames[property.DataModelPropertyName];

            if (!property.Dimensions.HasValue)
            {
                throw new VectorStoreOperationException($"Cannot create a collection, {nameof(property.Dimensions)} should be specified for {vectorPropertyName} vector property.");
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
            vectorIndexes.Add(vectorIndexPath);
        }

        var vectorEmbeddingPolicy = new VectorEmbeddingPolicy(embeddings);
        var indexingPolicy = new IndexingPolicy { VectorIndexes = vectorIndexes };

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

    private QueryDefinition GetSelectQuery(List<string> keys, List<string> fields)
    {
        var selectFields = fields.Select(field => $"x.{field}");
        var ids = string.Join(",", keys.Select((id, index) => $"@id{index}"));

        var whereClause = keys.Count == 1 ?
            $"WHERE x.{this._keyStoragePropertyName} = @id0" :
            $"WHERE x.{this._keyStoragePropertyName} IN ({ids})";

        var query = $"SELECT {string.Join(",", selectFields)} FROM x {whereClause}";

        var queryDefinition = new QueryDefinition(query);

        for (var i = 0; i < keys.Count; i++)
        {
            queryDefinition.WithParameter($"@id{i}", keys[i]);
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

            foreach (var record in response)
            {
                if (record is not null)
                {
                    yield return record;
                }
            }
        }
    }

    private async Task<string> UpsertItemAsync(string? key, string? partitionKeyValue, JsonNode item, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(key))
        {
            throw new VectorStoreOperationException($"Key property {this._keyProperty.DataModelPropertyName} is not initialized.");
        }

        PartitionKey? partitionKey = !string.IsNullOrWhiteSpace(partitionKeyValue) ?
            new PartitionKey(partitionKeyValue) :
            null;

        await this._database
            .GetContainer(this.CollectionName)
            .UpsertItemAsync(item, partitionKey, cancellationToken: cancellationToken)
            .ConfigureAwait(false);

        return key!;
    }

    private async Task DeleteItemsAsync(IEnumerable<string> keys, CancellationToken cancellationToken)
    {
        var fields = new HashSet<string> { AzureCosmosDBNoSQLConstants.ReservedKeyPropertyName, this._partitionKeyStoragePropertyName }.ToList();

        var query = this.GetSelectQuery(keys.ToList(), fields);

        // Get items from DB to obtain a partition key value, which is required for deletion operation.
        var items = await this.GetItemsAsync(query, cancellationToken)
            .ToListAsync(cancellationToken)
            .ConfigureAwait(false);

        var tasks = items.Select(item =>
        {
            var key = item[AzureCosmosDBNoSQLConstants.ReservedKeyPropertyName]!.ToString();
            var partitionKeyValue = item[this._partitionKeyStoragePropertyName]!.ToString();

            return this.RunOperationAsync("DeleteItem", () =>
                this._database
                    .GetContainer(this.CollectionName)
                    .DeleteItemAsync<JsonObject>(key, new PartitionKey(partitionKeyValue), cancellationToken: cancellationToken));
        });

        await Task.WhenAll(tasks).ConfigureAwait(false);
    }

    #endregion
}
