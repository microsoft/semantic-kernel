// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Weaviate.HttpV2;
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

    private readonly List<VectorStoreRecordDataProperty> _dataProperties;

    private readonly List<VectorStoreRecordVectorProperty> _vectorProperties;

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
        this._dataProperties = properties.DataProperties;
        this._vectorProperties = properties.VectorProperties;
    }

    /// <inheritdoc />
    public Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "GetCollectionSchema";

        return this.RunOperationAsync(OperationName, async () =>
        {
            using var request = new WeaviateGetCollectionSchemaRequest(this.CollectionName).Build();

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

            using var request = new WeaviateCreateCollectionSchemaRequest(schema).Build();

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
            using var request = new WeaviateDeleteCollectionSchemaRequest(this.CollectionName).Build();

            return this.ExecuteRequestAsync(request, cancellationToken);
        });
    }

    /// <inheritdoc />
    public Task DeleteAsync(Guid key, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc />
    public Task DeleteBatchAsync(IEnumerable<Guid> keys, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc />
    public Task<TRecord?> GetAsync(Guid key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc />
    public IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<Guid> keys, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc />
    public Task<Guid> UpsertAsync(TRecord record, UpsertRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc />
    public IAsyncEnumerable<Guid> UpsertBatchAsync(IEnumerable<TRecord> records, UpsertRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
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
