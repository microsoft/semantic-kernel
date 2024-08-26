// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class WeaviateVectorStoreRecordCollection<TRecord> : IVectorStoreRecordCollection<Guid, TRecord> where TRecord : class
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>The name of this database for telemetry purposes.</summary>
    private const string DatabaseName = "Weaviate";

    /// <summary>A set of types that a key on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedKeyTypes =
    [
        typeof(Guid)
    ];

    /// <summary>A set of types that vectors on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?),
        typeof(ReadOnlyMemory<double>),
        typeof(ReadOnlyMemory<double>?)
    ];

    private readonly HttpClient _httpClient;

    private readonly WeaviateVectorStoreRecordCollectionOptions<TRecord> _options;

    private readonly JsonSerializerOptions _jsonSerializerOptions;

    private readonly VectorStoreRecordDefinition _vectorStoreRecordDefinition;

    private readonly Dictionary<string, string> _storagePropertyNames;

    private readonly VectorStoreRecordKeyProperty _keyProperty;

    private readonly List<VectorStoreRecordDataProperty> _dataProperties;

    private readonly List<VectorStoreRecordVectorProperty> _vectorProperties;

    private readonly IVectorStoreRecordMapper<TRecord, JsonNode> _mapper;

    /// <inheritdoc />
    public string CollectionName { get; }

    public WeaviateVectorStoreRecordCollection(
        HttpClient httpClient,
        string collectionName,
        WeaviateVectorStoreRecordCollectionOptions<TRecord>? options = null)
    {
        // Verify.
        Verify.NotNull(httpClient);
        Verify.NotNullOrWhiteSpace(collectionName);

        // Assign.
        this._httpClient = httpClient;
        this.CollectionName = collectionName;
        this._options = options ?? new();
        this._jsonSerializerOptions = this._options.JsonSerializerOptions ?? JsonSerializerOptions.Default;
        this._vectorStoreRecordDefinition = this._options.VectorStoreRecordDefinition ?? VectorStoreRecordPropertyReader.CreateVectorStoreRecordDefinitionFromType(typeof(TRecord), supportsMultipleVectors: true);

        // Validate property types.
        var properties = VectorStoreRecordPropertyReader.SplitDefinitionAndVerify(typeof(TRecord).Name, this._vectorStoreRecordDefinition, supportsMultipleVectors: true, requiresAtLeastOneVector: false);
        VectorStoreRecordPropertyReader.VerifyPropertyTypes([properties.KeyProperty], s_supportedKeyTypes, "Key");
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(properties.VectorProperties, s_supportedVectorTypes, "Vector");

        // Assign properties and names for later usage.
        this._storagePropertyNames = VectorStoreRecordPropertyReader.BuildPropertyNameToJsonPropertyNameMap(properties, typeof(TRecord), this._jsonSerializerOptions);
        this._keyProperty = properties.KeyProperty;
        this._dataProperties = properties.DataProperties;
        this._vectorProperties = properties.VectorProperties;

        // Assign mapper.
        this._mapper = this._options.JsonNodeCustomMapper ??
            new WeaviateVectorStoreRecordMapper<TRecord>(
                this.CollectionName,
                this._keyProperty,
                this._dataProperties,
                this._vectorProperties,
                this._storagePropertyNames,
                this._jsonSerializerOptions);
    }

    /// <inheritdoc />
    public Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "GetCollectionSchema";

        return this.RunOperationAsync(OperationName, async () =>
        {
            var request = new WeaviateGetCollectionSchemaRequest(this.CollectionName).Build();

            var response = await this
                .ExecuteRequestWithNotFoundHandlingAsync<WeaviateGetCollectionSchemaResponse>(request, cancellationToken)
                .ConfigureAwait(false);

            return response != null;
        });
    }

    /// <inheritdoc />
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "CreateCollectionSchema";

        return this.RunOperationAsync(OperationName, () =>
        {
            var schema = WeaviateVectorStoreCollectionCreateMapping.MapToSchema(
                this.CollectionName,
                this._dataProperties,
                this._vectorProperties,
                this._storagePropertyNames);

            var request = new WeaviateCreateCollectionSchemaRequest(schema).Build();

            return this.ExecuteRequestAsync(request, cancellationToken);
        });
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
        const string OperationName = "DeleteCollectionSchema";

        return this.RunOperationAsync(OperationName, () =>
        {
            var request = new WeaviateDeleteCollectionSchemaRequest(this.CollectionName).Build();

            return this.ExecuteRequestAsync(request, cancellationToken);
        });
    }

    /// <inheritdoc />
    public Task DeleteAsync(Guid key, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "DeleteObject";

        return this.RunOperationAsync(OperationName, () =>
        {
            var request = new WeaviateDeleteObjectRequest(this.CollectionName, key).Build();

            return this.ExecuteRequestAsync(request, cancellationToken);
        });
    }

    /// <inheritdoc />
    public Task DeleteBatchAsync(IEnumerable<Guid> keys, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "DeleteObjectBatch";
        const string EqualOperand = "Equal";

        return this.RunOperationAsync(OperationName, () =>
        {
            var match = new WeaviateQueryMatch
            {
                CollectionName = this.CollectionName,
                WhereClause = new WeaviateQueryMatchWhereClause
                {
                    Operands =
                    [
                        new()
                        {
                            Operator = EqualOperand,
                            Path = [WeaviateConstants.ReservedKeyPropertyName],
                            Values = keys.Select(key => key.ToString()).ToList()
                        }
                    ]
                }
            };

            var request = new WeaviateDeleteObjectBatchRequest(match).Build();

            return this.ExecuteRequestAsync(request, cancellationToken);
        });
    }

    /// <inheritdoc />
    public Task<TRecord?> GetAsync(Guid key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "GetCollectionObject";

        return this.RunOperationAsync(OperationName, async () =>
        {
            var request = new WeaviateGetCollectionObjectRequest(this.CollectionName, key).Build();

            var jsonNode = await this.ExecuteRequestAsync<JsonNode>(request, cancellationToken).ConfigureAwait(false);

            if (jsonNode is null)
            {
                return null;
            }

            return VectorStoreErrorHandler.RunModelConversion(
                DatabaseName,
                this.CollectionName,
                OperationName,
                () => this._mapper.MapFromStorageToDataModel(jsonNode!, new()));
        });
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetBatchAsync(
        IEnumerable<Guid> keys,
        GetRecordOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var tasks = keys.Select(key => this.GetAsync(key, options, cancellationToken));

        var records = await Task.WhenAll(tasks).ConfigureAwait(false);

        foreach (var record in records)
        {
            if (record is not null)
            {
                yield return record;
            }
        }
    }

    /// <inheritdoc />
    public Task<Guid> UpsertAsync(TRecord record, UpsertRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "UpsertCollectionObject";

        return this.RunOperationAsync(OperationName, async () =>
        {
            var jsonNode = VectorStoreErrorHandler.RunModelConversion(
                DatabaseName,
                this.CollectionName,
                OperationName,
                () => this._mapper.MapFromDataToStorageModel(record));

            if (!Guid.TryParse(jsonNode[WeaviateConstants.ReservedKeyPropertyName]?.ToString(), out var recordId))
            {
                throw new VectorStoreOperationException($"Property '{WeaviateConstants.ReservedKeyPropertyName}' should be initialized before {OperationName} operation.");
            }

            var request = new WeaviateUpsertCollectionObjectRequest(this.CollectionName, recordId, jsonNode).Build();

            var resultJsonNode = await this.ExecuteRequestAsync<JsonNode>(request, cancellationToken).ConfigureAwait(false);

            if (resultJsonNode is null || !Guid.TryParse(resultJsonNode[WeaviateConstants.ReservedKeyPropertyName]?.ToString(), out var resultRecordId))
            {
                throw new VectorStoreOperationException($"Cannot get '{WeaviateConstants.ReservedKeyPropertyName}' property after {OperationName} operation.");
            }

            return resultRecordId;
        });
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<Guid> UpsertBatchAsync(
        IEnumerable<TRecord> records,
        UpsertRecordOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        const string OperationName = "UpsertCollectionObject";

        var results = await this.RunOperationAsync(OperationName, async () =>
        {
            var jsonNodes = records.Select(record => VectorStoreErrorHandler.RunModelConversion(
                DatabaseName,
                this.CollectionName,
                OperationName,
                () => this._mapper.MapFromDataToStorageModel(record))).ToList();

            var request = new WeaviateUpsertCollectionObjectBatchRequest(jsonNodes).Build();

            return await this.ExecuteRequestAsync<List<JsonNode>>(request, cancellationToken).ConfigureAwait(false);
        }).ConfigureAwait(false);

        if (results is not null)
        {
            foreach (var result in results)
            {
                if (result is not null && Guid.TryParse(result[WeaviateConstants.ReservedKeyPropertyName]?.ToString(), out var resultRecordId))
                {
                    yield return resultRecordId;
                }
            }
        }
    }

    #region private

    private Task<HttpResponseMessage> ExecuteRequestAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        return this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken);
    }

    private async Task<TResponse?> ExecuteRequestAsync<TResponse>(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        var response = await this.ExecuteRequestAsync(request, cancellationToken).ConfigureAwait(false);

        var responseContent = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        return JsonSerializer.Deserialize<TResponse>(responseContent, this._jsonSerializerOptions);
    }

    private async Task<TResponse?> ExecuteRequestWithNotFoundHandlingAsync<TResponse>(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        try
        {
            return await this.ExecuteRequestAsync<TResponse>(request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException ex) when (ex.StatusCode == HttpStatusCode.NotFound)
        {
            return default;
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

    #endregion
}
