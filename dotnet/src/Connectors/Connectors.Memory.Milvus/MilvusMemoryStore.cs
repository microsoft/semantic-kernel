// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Memory;
using Milvus.Client;

namespace Microsoft.SemanticKernel.Connectors.Memory.Milvus;

/// <summary>
/// An implementation of <see cref="IMemoryStore" /> for the Milvus vector database.
/// </summary>
public class MilvusMemoryStore : IMemoryStore, IDisposable
{
    private readonly int _vectorSize;
    private readonly SimilarityMetricType _metricType;
    private readonly bool _ownsMilvusClient;

    private const string IsReferenceFieldName = "is_reference";
    private const string ExternalSourceNameFieldName = "external_source_name";
    private const string IdFieldName = "id";
    private const string DescriptionFieldName = "description";
    private const string TextFieldName = "text";
    private const string AdditionalMetadataFieldName = "additional_metadata";
    private const string EmbeddingFieldName = "embedding";
    private const string KeyFieldName = "key";
    private const string TimestampFieldName = "timestamp";

    private const int DefaultMilvusPort = 19530;
    private const ConsistencyLevel DefaultConsistencyLevel = ConsistencyLevel.Session;
    private const int DefaultVarcharLength = 65_535;

    private readonly QueryParameters _queryParametersWithEmbedding = new()
    {
        OutputFields = { IsReferenceFieldName, ExternalSourceNameFieldName, IdFieldName, DescriptionFieldName, TextFieldName, AdditionalMetadataFieldName, EmbeddingFieldName, KeyFieldName, TimestampFieldName }
    };

    private readonly QueryParameters _queryParametersWithoutEmbedding = new()
    {
        OutputFields = { IsReferenceFieldName, ExternalSourceNameFieldName, IdFieldName, DescriptionFieldName, TextFieldName, AdditionalMetadataFieldName, KeyFieldName, TimestampFieldName }
    };

    private readonly SearchParameters _searchParameters = new()
    {
        OutputFields = { IsReferenceFieldName, ExternalSourceNameFieldName, IdFieldName, DescriptionFieldName, TextFieldName, AdditionalMetadataFieldName, KeyFieldName, TimestampFieldName }
    };

    /// <summary>
    /// Exposes the underlying <see cref="Client" /> used to communicate with Milvus. Can be used to execute operations not supported by the <see cref="IMemoryStore" /> abstraction.
    /// </summary>
    public MilvusClient Client { get; }

    #region Constructors

    /// <summary>
    /// Creates a new <see cref="MilvusMemoryStore" />, connecting to the given hostname on the default Milvus port of 19530.
    /// For more advanced configuration opens, construct a <see cref="MilvusClient" /> instance and pass it to
    /// <see cref="MilvusMemoryStore(MilvusClient, int, SimilarityMetricType)" />.
    /// </summary>
    /// <param name="host">The hostname or IP address to connect to.</param>
    /// <param name="port">The port to connect to. Defaults to 19530.</param>
    /// <param name="ssl">Whether to use TLS/SSL. Defaults to <c>false</c>.</param>
    /// <param name="database">The database to connect to. Defaults to the default Milvus database.</param>
    /// <param name="vectorSize">The size of the vectors used in Milvus. Defaults to 1536.</param>
    /// <param name="metricType">The metric used to measure similarity between vectors. Defaults to <see cref="SimilarityMetricType.Ip" />.</param>
    /// <param name="loggerFactory">An optional logger factory through which the Milvus client will log.</param>
    public MilvusMemoryStore(
        string host,
        int port = DefaultMilvusPort,
        bool ssl = false,
        string? database = null,
        int vectorSize = 1536,
        SimilarityMetricType metricType = SimilarityMetricType.Ip,
        ILoggerFactory? loggerFactory = null)
        : this(new MilvusClient(host, port, ssl, database, callOptions: default, loggerFactory), vectorSize, metricType)
    {
        this._ownsMilvusClient = true;
    }

    /// <summary>
    /// Creates a new <see cref="MilvusMemoryStore" />, connecting to the given hostname on the default Milvus port of 19530.
    /// For more advanced configuration opens, construct a <see cref="MilvusClient" /> instance and pass it to
    /// <see cref="MilvusMemoryStore(MilvusClient, int, SimilarityMetricType)" />.
    /// </summary>
    /// <param name="host">The hostname or IP address to connect to.</param>
    /// <param name="username">The username to use for authentication.</param>
    /// <param name="password">The password to use for authentication.</param>
    /// <param name="port">The port to connect to. Defaults to 19530.</param>
    /// <param name="ssl">Whether to use TLS/SSL. Defaults to <c>false</c>.</param>
    /// <param name="database">The database to connect to. Defaults to the default Milvus database.</param>
    /// <param name="vectorSize">The size of the vectors used in Milvus. Defaults to 1536.</param>
    /// <param name="metricType">The metric used to measure similarity between vectors. Defaults to <see cref="SimilarityMetricType.Ip" />.</param>
    /// <param name="loggerFactory">An optional logger factory through which the Milvus client will log.</param>
    public MilvusMemoryStore(
        string host,
        string username,
        string password,
        int port = DefaultMilvusPort,
        bool ssl = false,
        string? database = null,
        int vectorSize = 1536,
        SimilarityMetricType metricType = SimilarityMetricType.Ip,
        ILoggerFactory? loggerFactory = null)
        : this(new MilvusClient(host, username, password, port, ssl, database, callOptions: default, loggerFactory), vectorSize, metricType)
    {
        this._ownsMilvusClient = true;
    }

    /// <summary>
    /// Creates a new <see cref="MilvusMemoryStore" />, connecting to the given hostname on the default Milvus port of 19530.
    /// For more advanced configuration opens, construct a <see cref="MilvusClient" /> instance and pass it to
    /// <see cref="MilvusMemoryStore(MilvusClient, int, SimilarityMetricType)" />.
    /// </summary>
    /// <param name="host">The hostname or IP address to connect to.</param>
    /// <param name="apiKey">An API key to be used for authentication, instead of a username and password.</param>
    /// <param name="port">The port to connect to. Defaults to 19530.</param>
    /// <param name="ssl">Whether to use TLS/SSL. Defaults to <c>false</c>.</param>
    /// <param name="database">The database to connect to. Defaults to the default Milvus database.</param>
    /// <param name="vectorSize">The size of the vectors used in Milvus. Defaults to 1536.</param>
    /// <param name="metricType">The metric used to measure similarity between vectors. Defaults to <see cref="SimilarityMetricType.Ip" />.</param>
    /// <param name="loggerFactory">An optional logger factory through which the Milvus client will log.</param>
    public MilvusMemoryStore(
        string host,
        string apiKey,
        int port = DefaultMilvusPort,
        bool ssl = false,
        string? database = null,
        int vectorSize = 1536,
        SimilarityMetricType metricType = SimilarityMetricType.Ip,
        ILoggerFactory? loggerFactory = null)
        : this(new MilvusClient(host, apiKey, port, ssl, database, callOptions: default, loggerFactory), vectorSize, metricType)
    {
        this._ownsMilvusClient = true;
    }

    /// <summary>
    /// Initializes a new instance of <see cref="MilvusMemoryStore" /> over the given <see cref="MilvusClient" />.
    /// </summary>
    /// <param name="client">A <see cref="MilvusClient" /> configured with the necessary endpoint and authentication information.</param>
    /// <param name="vectorSize">The size of the vectors used in Milvus. Defaults to 1536.</param>
    /// <param name="metricType">The metric used to measure similarity between vectors. Defaults to <see cref="SimilarityMetricType.Ip" />.</param>
    public MilvusMemoryStore(
        MilvusClient client,
        int vectorSize = 1536,
        SimilarityMetricType metricType = SimilarityMetricType.Ip)
        : this(client, ownsMilvusClient: false, vectorSize, metricType)
    {
    }

    private MilvusMemoryStore(
        MilvusClient client,
        bool ownsMilvusClient,
        int vectorSize = 1536,
        SimilarityMetricType metricType = SimilarityMetricType.Ip)
    {
        this.Client = client;
        this._vectorSize = vectorSize;
        this._metricType = metricType;
        this._ownsMilvusClient = ownsMilvusClient;
    }

    #endregion Constructors

    /// <inheritdoc />
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        var exists = await this.Client.HasCollectionAsync(collectionName, cancellationToken: cancellationToken).ConfigureAwait(false);
        if (!exists)
        {
            CollectionSchema schema = new()
            {
                Fields =
                {
                    FieldSchema.CreateVarchar(IdFieldName, maxLength: DefaultVarcharLength, isPrimaryKey: true, autoId: false),
                    FieldSchema.CreateFloatVector(EmbeddingFieldName, this._vectorSize)
                },
                EnableDynamicFields = true
            };

            MilvusCollection collection = await this.Client.CreateCollectionAsync(collectionName, schema, DefaultConsistencyLevel, cancellationToken: cancellationToken).ConfigureAwait(false);

            await collection.CreateIndexAsync(EmbeddingFieldName, metricType: this._metricType, cancellationToken: cancellationToken).ConfigureAwait(false);
            await collection.WaitForIndexBuildAsync("float_vector", cancellationToken: cancellationToken).ConfigureAwait(false);

            await collection.LoadAsync(cancellationToken: cancellationToken).ConfigureAwait(false);
            await collection.WaitForCollectionLoadAsync(waitingInterval: TimeSpan.FromMilliseconds(100), timeout: TimeSpan.FromMinutes(1), cancellationToken: cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (MilvusCollectionInfo collection in await this.Client.ListCollectionsAsync(cancellationToken: cancellationToken).ConfigureAwait(false))
        {
            yield return collection.Name;
        }
    }

    /// <inheritdoc />
    public Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
        => this.Client.HasCollectionAsync(collectionName, cancellationToken: cancellationToken);

    /// <inheritdoc />
    public Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
        => this.Client.GetCollection(collectionName).DropAsync(cancellationToken);

    /// <inheritdoc />
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        MilvusCollection collection = this.Client.GetCollection(collectionName);

        await collection.DeleteAsync($@"{IdFieldName} in [""{record.Metadata.Id}""]", cancellationToken: cancellationToken).ConfigureAwait(false);

        var metadata = record.Metadata;

        List<FieldData> fieldData = new()
        {
            FieldData.Create(IdFieldName, new[] { metadata.Id }),
            FieldData.CreateFloatVector(EmbeddingFieldName, new[] { record.Embedding }),

            FieldData.Create(IsReferenceFieldName, new[] { metadata.IsReference }, isDynamic: true),
            FieldData.Create(ExternalSourceNameFieldName, new[] { metadata.ExternalSourceName }, isDynamic: true),
            FieldData.Create(DescriptionFieldName, new[] { metadata.Description }, isDynamic: true),
            FieldData.Create(TextFieldName, new[] { metadata.Text }, isDynamic: true),
            FieldData.Create(AdditionalMetadataFieldName, new[] { metadata.AdditionalMetadata }, isDynamic: true),
            FieldData.Create(KeyFieldName, new[] { record.Key }, isDynamic: true),
            FieldData.Create(TimestampFieldName, new[] { record.Timestamp?.ToString(CultureInfo.InvariantCulture) ?? string.Empty }, isDynamic: true)
        };

        MutationResult result = await collection.InsertAsync(fieldData, cancellationToken: cancellationToken).ConfigureAwait(false);

        return result.Ids.StringIds![0];
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> UpsertBatchAsync(
        string collectionName,
        IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        // TODO: Milvus v2.3.0 will have a 1st-class upsert API which we should use.
        // In the meantime, we do delete+insert, following the Python connector's example.

        StringBuilder idString = new();

        List<bool> isReferenceData = new();
        List<string> externalSourceNameData = new();
        List<string> idData = new();
        List<string> descriptionData = new();
        List<string> textData = new();
        List<string> additionalMetadataData = new();
        List<ReadOnlyMemory<float>> embeddingData = new();
        List<string> keyData = new();
        List<string> timestampData = new();

        foreach (MemoryRecord record in records)
        {
            var metadata = record.Metadata;

            if (idString.Length > 0)
            {
                idString.Append(',');
            }

            idString.Append('"').Append(metadata.Id).Append('"');

            isReferenceData.Add(metadata.IsReference);
            externalSourceNameData.Add(metadata.ExternalSourceName);
            idData.Add(record.Metadata.Id);
            descriptionData.Add(metadata.Description);
            textData.Add(metadata.Text);
            additionalMetadataData.Add(metadata.AdditionalMetadata);
            embeddingData.Add(record.Embedding);
            keyData.Add(record.Key);
            timestampData.Add(record.Timestamp?.ToString(CultureInfo.InvariantCulture) ?? string.Empty);
        }

        MilvusCollection collection = this.Client.GetCollection(collectionName);
        await collection.DeleteAsync($"{IdFieldName} in [{idString}]", cancellationToken: cancellationToken).ConfigureAwait(false);

        FieldData[] fieldData =
        {
            FieldData.Create(IdFieldName, idData),
            FieldData.CreateFloatVector(EmbeddingFieldName, embeddingData),

            FieldData.Create(IsReferenceFieldName, isReferenceData, isDynamic: true),
            FieldData.Create(ExternalSourceNameFieldName, externalSourceNameData, isDynamic: true),
            FieldData.Create(DescriptionFieldName, descriptionData, isDynamic: true),
            FieldData.Create(TextFieldName, textData, isDynamic: true),
            FieldData.Create(AdditionalMetadataFieldName, additionalMetadataData, isDynamic: true),
            FieldData.Create(KeyFieldName, keyData, isDynamic: true),
            FieldData.Create(TimestampFieldName, timestampData, isDynamic: true)
        };

        MutationResult result = await collection.InsertAsync(fieldData, cancellationToken: cancellationToken).ConfigureAwait(false);

        foreach (var id in result.Ids.StringIds!)
        {
            yield return id;
        }
    }

    /// <inheritdoc />
    public async Task<MemoryRecord?> GetAsync(
        string collectionName,
        string key,
        bool withEmbedding = false,
        CancellationToken cancellationToken = default)
    {
        await foreach (MemoryRecord record in this.GetBatchAsync(collectionName, new[] { key }, withEmbedding, cancellationToken))
        {
            return record;
        }

        return null;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(
        string collectionName,
        IEnumerable<string> keys,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        StringBuilder idString = new();

        foreach (string key in keys)
        {
            if (idString.Length > 0)
            {
                idString.Append(',');
            }

            idString.Append('"').Append(key).Append('"');
        }

        IReadOnlyList<FieldData> fields = await this.Client
            .GetCollection(collectionName)
            .QueryAsync($"{IdFieldName} in [{idString}]", withEmbeddings ? this._queryParametersWithEmbedding : this._queryParametersWithoutEmbedding, cancellationToken: cancellationToken)
            .ConfigureAwait(false);

        var rowCount = fields[0].RowCount;

        for (int rowNum = 0; rowNum < rowCount; rowNum++)
        {
            yield return this.ReadMemoryRecord(fields, rowNum);
        }
    }

    /// <inheritdoc />
    public Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default)
        => this.Client.GetCollection(collectionName)
            .DeleteAsync($@"{IdFieldName} in [""{key}""]", cancellationToken: cancellationToken);

    /// <inheritdoc />
    public Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        StringBuilder idString = new();

        idString.Append(IdFieldName).Append(" in [");

        bool first = true;
        foreach (string id in keys)
        {
            if (first)
            {
                first = false;
            }
            else
            {
                idString.Append(',');
            }

            idString.Append('"').Append(id).Append('"');
        }

        idString.Append(']');

        return this.Client
            .GetCollection(collectionName)
            .DeleteAsync(idString.ToString(), cancellationToken: cancellationToken);
    }

    /// <inheritdoc />
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(
        string collectionName,
        ReadOnlyMemory<float> embedding,
        double minRelevanceScore = 0,
        bool withEmbedding = false,
        CancellationToken cancellationToken = default)
    {
        await foreach ((MemoryRecord, double) result in this.GetNearestMatchesAsync(collectionName, embedding, limit: 1, minRelevanceScore, withEmbedding, cancellationToken))
        {
            return result;
        }

        return null;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        ReadOnlyMemory<float> embedding,
        int limit,
        double minRelevanceScore = 0,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        MilvusCollection collection = this.Client.GetCollection(collectionName);

        SearchResults results = await collection
            .SearchAsync(EmbeddingFieldName, new[] { embedding }, SimilarityMetricType.Ip, limit, this._searchParameters, cancellationToken)
            .ConfigureAwait(false);

        IReadOnlyList<string> ids = results.Ids.StringIds!;
        int rowCount = ids.Count;
        IReadOnlyList<FieldData> data = results.FieldsData;

        // Since Milvus does not support fetching vectors via the Search API, we do an extra call to fetch the ids and embeddings using the Query API,
        // using the IDs returned from the Search above, populating a map from the IDs to the embedding.
        // TODO: There's some support for fetching vectors from Search in Milvus 2.3, check that out.
        Dictionary<string, ReadOnlyMemory<float>>? embeddingMap = null;
        if (withEmbeddings)
        {
            StringBuilder filter = new();
            filter.Append(IdFieldName).Append(" in [");

            for (int rowNum = 0; rowNum < ids.Count; rowNum++)
            {
                if (rowNum > 0)
                {
                    filter.Append(',');
                }

                filter.Append('"').Append(ids[rowNum]).Append('"');
            }

            filter.Append(']');

            IReadOnlyList<FieldData> fieldData = await collection.QueryAsync(
                    filter.ToString(),
                    new() { OutputFields = { EmbeddingFieldName } },
                    cancellationToken: cancellationToken)
                .ConfigureAwait(false);

            IReadOnlyList<string> idData = (fieldData[0] as FieldData<string> ?? fieldData[1] as FieldData<string>)!.Data;
            IReadOnlyList<ReadOnlyMemory<float>> embeddingData = (fieldData[0] as FloatVectorFieldData ?? fieldData[1] as FloatVectorFieldData)!.Data;

            embeddingMap = new Dictionary<string, ReadOnlyMemory<float>>(ids.Count);
            for (int rowNum = 0; rowNum < ids.Count; rowNum++)
            {
                embeddingMap[idData[rowNum]] = embeddingData[rowNum];
            }
        }

        for (int rowNum = 0; rowNum < rowCount; rowNum++)
        {
            // TODO: Milvus 2.3 has range search, which will move this to the server.
            if (results.Scores[rowNum] >= minRelevanceScore)
            {
                yield return (
                    this.ReadMemoryRecord(data, rowNum, withEmbeddings ? embeddingMap![ids[rowNum]] : null),
                    results.Scores[rowNum]);
            }
        }
    }

    private MemoryRecord ReadMemoryRecord(IReadOnlyList<FieldData> data, int rowNum, ReadOnlyMemory<float>? externalEmbedding = null)
    {
        bool isReference = false;
        string externalSourceName = string.Empty;
        string id = string.Empty;
        string description = string.Empty;
        string text = string.Empty;
        string additionalMetadata = string.Empty;
        ReadOnlyMemory<float>? embedding = null;
        string key = string.Empty;
        DateTimeOffset? timestamp = null;

        foreach (FieldData field in data)
        {
            switch (field.FieldName)
            {
                case IsReferenceFieldName when field is FieldData<bool> isReferenceField:
                    isReference = isReferenceField.Data[rowNum];
                    break;

                case ExternalSourceNameFieldName when field is FieldData<string> externalSourceNameField:
                    externalSourceName = externalSourceNameField.Data[rowNum];
                    break;

                case IdFieldName when field is FieldData<string> idField:
                    id = idField.Data[rowNum];
                    break;

                case DescriptionFieldName when field is FieldData<string> descriptionField:
                    description = descriptionField.Data[rowNum];
                    break;

                case TextFieldName when field is FieldData<string> textField:
                    text = textField.Data[rowNum];
                    break;

                case AdditionalMetadataFieldName when field is FieldData<string> additionalMetadataField:
                    additionalMetadata = additionalMetadataField.Data[rowNum];
                    break;

                case EmbeddingFieldName when field is FloatVectorFieldData embeddingField:
                    Debug.Assert(externalEmbedding is null);
                    embedding = embeddingField.Data[rowNum];
                    break;

                case KeyFieldName when field is FieldData<string> keyField:
                    key = keyField.Data[rowNum];
                    break;

                case TimestampFieldName when field is FieldData<string> timestampField:
                    string timestampString = timestampField.Data[rowNum];
                    timestamp = timestampString is { Length: > 0 }
                        ? DateTimeOffset.Parse(timestampString, CultureInfo.InvariantCulture)
                        : null;
                    break;

                default:
                    continue; // Unknown field - ignore
            }
        }

        return new MemoryRecord(
            new MemoryRecordMetadata(isReference, id, text, description, externalSourceName, additionalMetadata),
            embedding ?? externalEmbedding ?? Array.Empty<float>(),
            key,
            timestamp);
    }

    /// <summary>
    /// Implements the dispose pattern.
    /// </summary>
    protected virtual void Dispose(bool disposing)
    {
        if (disposing && this._ownsMilvusClient)
        {
            this.Client.Dispose();
        }
    }

    /// <inheritdoc />
    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }
}
