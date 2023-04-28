// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone;

internal sealed class PineconeClient : IPineconeClient, IDisposable
{

    internal PineconeClient(PineconeEnvironment pineconeEnvironment, string apiKey, ILogger? logger = null)
    {
        this._pineconeEnvironment = pineconeEnvironment;
        this._authHeader = new KeyValuePair<string, string>("Api-Key", apiKey);
        this._jsonSerializerOptions = PineconeUtils.DefaultSerializerOptions;
        this._logger = logger ?? NullLogger<PineconeClient>.Instance;
        this._httpClient = new HttpClient(HttpHandlers.CheckCertificateRevocation);
    }

    /// <inheritdoc />
    public string IndexName => this._indexDescription?.Configuration.Name ?? string.Empty;

    /// <inheritdoc />
    public string Host => this._indexDescription?.Status.Host ?? string.Empty;

    /// <inheritdoc />
    public int Port => this._indexDescription != null ? this._indexDescription.Status.Port : 0;

    /// <inheritdoc />
    public IndexState State => this._indexDescription?.Status.State ?? IndexState.None;

    /// <inheritdoc />
    public bool Ready => this._indexDescription?.Status.Ready ?? false;

    /// <inheritdoc />
    public async IAsyncEnumerable<PineconeDocument?> FetchVectorsAsync(
        string indexName,
        IEnumerable<string> ids,
        string @namespace = "",
        bool includeValues = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this._logger.LogInformation("Searching vectors by id");

        if (!this.Ready)
        {
            this._logger.LogWarning("Index is not ready");
            yield break;
        }
        //
        string basePath = await this.GetVectorOperationsApiBasePathAsync(indexName).ConfigureAwait(false);

        FetchRequest fetchRequest = FetchRequest.FetchVectors(ids)
            .FromNamespace(@namespace);

        using HttpRequestMessage request = fetchRequest.Build();

        request.Headers.Add("accept", "application/json");

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(basePath, request,
            cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e)
        {
            this._logger.LogDebug("Vectors not found {0}", e.Message);
            yield break;
        }

        FetchResponse? data = JsonSerializer.Deserialize<FetchResponse>(responseContent, this._jsonSerializerOptions);

        if (data == null)
        {
            this._logger.LogWarning("Unable to deserialize Get response");
            yield break;
        }

        if (!data.Vectors.Any())
        {
            this._logger.LogWarning("Vectors not found");
            yield break;
        }

        IEnumerable<PineconeDocument> records = includeValues
            ? data.Vectors.Values
            : data.WithoutEmbeddings();

#pragma warning disable CS8604 // The request specifically asked for a payload to be in the response
        foreach (PineconeDocument? record in records)
        {

            yield return record;
        }

    }

    /// <inheritdoc />
    public async IAsyncEnumerable<PineconeDocument?> QueryAsync(
        string indexName,
        int topK,
        string @namespace = "",
        IEnumerable<float>? vector = default,
        bool includeValues = false,
        bool includeMetadata = true,
        Dictionary<string, object>? filter = null,
        SparseVectorData? sparseVector = null,
        string? id = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this._logger.LogInformation("Querying top {0} nearest vectors", topK);

        if (!this.Ready)
        {
            this._logger.LogWarning("Index is not ready");
            yield break;
        }

        using HttpRequestMessage request = QueryRequest.QueryIndex(vector)
            .WithTopK(topK)
            .InNamespace(@namespace)
            .WithFilter(filter)
            .WithMetadata(includeMetadata)
            .WithVectors(includeValues)
            .WithSparseVector(sparseVector)
            .WithId(id)
            .Build();

        request.Headers.Add("accept", "application/json");

        string basePath = await this.GetVectorOperationsApiBasePathAsync(indexName).ConfigureAwait(false);

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(basePath, request, cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e)
        {
            this._logger.LogDebug("Vectors not found {0}", e.Message);
            yield break;
        }

        QueryResponse? queryResponse = JsonSerializer.Deserialize<QueryResponse>(responseContent, this._jsonSerializerOptions);

        if (queryResponse == null)
        {
            this._logger.LogWarning("Unable to deserialize Query response");
            yield break;
        }

        if (!queryResponse.Matches.Any())
        {
            this._logger.LogWarning("No matches found");
            yield break;
        }

        foreach (PineconeDocument? match in queryResponse.Matches)
        {
            yield return match;
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<(PineconeDocument, double)> GetMostRelevantAsync(
        string indexName,
        IEnumerable<float> vector,
        double threshold,
        int topK,
        bool includeValues,
        bool includeMetadata,
        string? @namespace = default,
        Dictionary<string, object>? filter = default,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this._logger.LogInformation("Searching top {0} nearest vectors with threshold {1}", topK, threshold);

        if (!this.Ready)
        {
            this._logger.LogWarning("Index is not ready");
            yield break;
        }

        List<(PineconeDocument document, float score)> documents = new();

        IAsyncEnumerable<PineconeDocument?> matches = this.QueryAsync(
            indexName,
            topK,
            @namespace,
            vector,
            includeValues,
            includeMetadata,
            filter, null, null, cancellationToken);

        await foreach (PineconeDocument? match in matches.WithCancellation(cancellationToken))
        {
            if (match == null)
            {
                continue;
            }

            if (match.Score > threshold)
            {
                documents.Add((match, match.Score ?? 0));
            }
        }

        if (!documents.Any())
        {
            this._logger.LogWarning("No relevant documents found");
            yield break;
        }

        // sort documents by score, and order by ascending
        documents = documents.OrderByDescending(x => x.score).ToList();

        foreach ((PineconeDocument document, float score) in documents)
        {
            yield return (document, score);
        }
    }

    /// <inheritdoc />
    public async Task<int> UpsertAsync(
        string indexName,
        IEnumerable<PineconeDocument> vectors,
        string @namespace = "",
        CancellationToken cancellationToken = default)
    {
        this._logger.LogInformation("Upserting vectors");

        if (!this.Ready)
        {
            this._logger.LogWarning("Index is not ready");
            return 0;
        }

        int totalUpserted = 0;
        int totalBatches = 0;

        string basePath = await this.GetVectorOperationsApiBasePathAsync(indexName).ConfigureAwait(false);
        IAsyncEnumerable<PineconeDocument> validVectors = PineconeUtils.EnsureValidMetadataAsync(vectors.ToAsyncEnumerable());

        await foreach (UpsertRequest? batch in PineconeUtils.GetUpsertBatchesAsync(validVectors, MaxBatchSize).WithCancellation(cancellationToken))
        {
            totalBatches++;
            HttpRequestMessage request = batch.ToNamespace(@namespace).Build();
            request.Headers.Add("accept", "application/json");

            (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(basePath, request, cancellationToken).ConfigureAwait(false);

            try
            {
                response.EnsureSuccessStatusCode();
            }
            catch (HttpRequestException e)
            {
                this._logger.LogDebug("Failed to upsert vectors {0}", e.Message);
                throw;
            }

            UpsertResponse? data = JsonSerializer.Deserialize<UpsertResponse>(responseContent, this._jsonSerializerOptions);

            if (data == null)
            {
                this._logger.LogWarning("Unable to deserialize Upsert response");
                continue;
            }

            totalUpserted += data.UpsertedCount;
            this._logger.LogInformation("Upserted batch {0} with {1} vectors", totalBatches, data.UpsertedCount);
            await Task.Delay(TimeSpan.FromMilliseconds(1000), cancellationToken).ConfigureAwait(true);
        }

        this._logger.LogInformation("Upserted {0} vectors in {1} batches", totalUpserted, totalBatches);
        return totalUpserted;
    }

    /// <inheritdoc />
    public async Task DeleteAsync(
        string indexName,
        IEnumerable<string>? ids = null,
        string @namespace = "",
        Dictionary<string, object>? filter = null,
        bool deleteAll = false,
        CancellationToken cancellationToken = default)
    {

        if (!this.Ready)
        {
            this._logger.LogWarning("Index is not ready");
            return;
        }

        if (ids == null && string.IsNullOrEmpty(@namespace) && filter == null && !deleteAll)
        {
            throw new ArgumentException("Must provide at least one of ids, filter, or deleteAll");
        }

        ids = ids?.ToList();

        DeleteRequest deleteRequest;

        switch (deleteAll)
        {
            case true when !string.IsNullOrEmpty(@namespace):
                this._logger.LogInformation("Deleting all vectors in namespace {0}", @namespace);
                deleteRequest = DeleteRequest.ClearNamespace(@namespace);
                break;
            case true:
                this._logger.LogInformation("Deleting all vectors in index {0}", indexName);
                deleteRequest = DeleteRequest.GetDeleteAllVectorsRequest();
                break;
            default:
            {
                if (ids != null && !string.IsNullOrEmpty(@namespace))
                {
                    if (filter != null)
                    {
                        this._logger.LogInformation("Deleting vectors {0} in namespace {1} with filter {2}", string.Join(",", ids), @namespace, filter);
                        deleteRequest = DeleteRequest.DeleteVectors(ids)
                            .FromNamespace(@namespace)
                            .FilterBy(filter);
                    }
                    else
                    {
                        this._logger.LogInformation("Deleting vectors {0} in namespace {1}", string.Join(",", ids), @namespace);
                        deleteRequest = DeleteRequest.DeleteVectors(ids)
                            .FromNamespace(@namespace);
                    }
                }

                else
                {
                    if (filter != null)
                    {
                        this._logger.LogInformation("Deleting vectors {0} with filter {1}", string.Join(",", ids), filter);
                        deleteRequest = DeleteRequest.DeleteVectors(ids)
                            .FilterBy(filter);
                    }
                    else
                    {
                        this._logger.LogInformation("Deleting vectors {0}", string.Join(",", ids));
                        deleteRequest = DeleteRequest.DeleteVectors(ids);
                    }
                }
                break;
            }
        }

        string basePath = await this.GetVectorOperationsApiBasePathAsync(indexName).ConfigureAwait(false);

        using HttpRequestMessage request = deleteRequest.Build();

        request.Headers.Add("accept", "application/json");

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(basePath, request, cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e)
        {
            this._logger.LogWarning("Vector update for Documents {0} failed. Message: {1}", string.Join(",", ids), e.Message);
        }
    }

    /// <inheritdoc />
    public async Task UpdateAsync(string indexName, PineconeDocument document, string @namespace = "", CancellationToken cancellationToken = default)
    {

        if (!this.Ready)
        {
            this._logger.LogWarning("Index is not ready");
            return;
        }

        this._logger.LogInformation("Updating vector: {0}", document.Id);

        string basePath = await this.GetVectorOperationsApiBasePathAsync(indexName).ConfigureAwait(false);

        using HttpRequestMessage request = UpdateVectorRequest
            .FromPineconeDocument(document)
            .InNamespace(@namespace)
            .Build();

        request.Headers.Add("accept", "application/json");

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(basePath, request, cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e)
        {
            this._logger.LogWarning("Vector update for Document {0} failed. Message: {1}", document.Id, e.Message);
        }
    }

    /// <inheritdoc />
    public async Task<IndexStats?> DescribeIndexStatsAsync(
        string indexName,
        Dictionary<string, object>? filter = default,
        CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Getting index stats for index {0}", indexName);

        string basePath = await this.GetVectorOperationsApiBasePathAsync(indexName).ConfigureAwait(false);

        using HttpRequestMessage request = DescribeIndexStatsRequest.GetIndexStats()
            .WithFilter(filter)
            .Build();

        request.Headers.Add("accept", "application/json");

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(basePath, request, cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e)
        {
            this._logger.LogDebug("Index not found {0}", e.Message);
            return null;
        }

        IndexStats? result = JsonSerializer.Deserialize<IndexStats>(responseContent, this._jsonSerializerOptions);

        if (result != null)
        {
            this._logger.LogDebug("Index stats retrieved");
        }
        else
        {
            this._logger.LogWarning("Index stats retrieval failed");
        }

        return result;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string?> ListIndexesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using HttpRequestMessage request = ListIndexesRequest.Create().Build();
        request.Headers.Add("accept", "application/json; charset=utf-8");

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(this.GetIndexOperationsApiBasePath(), request, cancellationToken).ConfigureAwait(false);

        string[]? indices = JsonSerializer.Deserialize<string[]?>(responseContent, this._jsonSerializerOptions);

        if (indices == null)
        {
            yield break;
        }

        foreach (string? index in indices)
        {
            yield return index;
        }
    }

    /// <inheritdoc />
    public async Task<string?> CreateIndexAsync(IndexDefinition indexDefinition, CancellationToken cancellationToken = default)
    {
        this._logger.LogInformation("Creating index {0} with metadata config: {1}", indexDefinition.Name, string.Join(",", indexDefinition.MetadataConfig?.Indexed));

        string indexName = indexDefinition.Name;
        using HttpRequestMessage request = indexDefinition.Build();

        request.Headers.Add("accept", "text/plain");

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(this.GetIndexOperationsApiBasePath(), request, cancellationToken).ConfigureAwait(false);

        switch (response.StatusCode)
        {
            case HttpStatusCode.BadRequest:
                this._logger.LogError("Bad Request: {0}, {1}", response.StatusCode, responseContent);
                return string.Empty;
            case HttpStatusCode.Conflict:
                this._logger.LogError("Index of given name already exists: {0}, {1}", response.StatusCode, responseContent);
                return string.Empty;
            default:
                try
                {
                    response.EnsureSuccessStatusCode();
                }

                catch (HttpRequestException e)
                {
                    this._logger.LogError(e, "Createing index failed: {0}, {1}", e.Message, responseContent);
                    throw;
                }

                this._logger.LogDebug("Index created: {0}, {1}", indexName, responseContent);
                break;
        }

        await this.WaitForIndexStateAsync(indexName, IndexState.Ready, cancellationToken).ConfigureAwait(false);

        return this._indexDescription?.Configuration.Name;
    }

    /// <inheritdoc />
    public async Task DeleteIndexAsync(string indexName, CancellationToken cancellationToken = default)
    {
        this._logger.LogInformation("Deleting index {0}", indexName);

        using HttpRequestMessage request = DeleteIndexRequest.Create(indexName).Build();

        request.Headers.Add("accept", "text/plain");

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(this.GetIndexOperationsApiBasePath(), request, cancellationToken).ConfigureAwait(false);

        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            this._logger.LogError("Index Not Found: {0}, {1}", response.StatusCode, responseContent);
            return;
        }

        try
        {
            response.EnsureSuccessStatusCode();

            if (response.StatusCode == HttpStatusCode.Accepted)
            {
                this._logger.LogDebug("Index: {0} been successfully deleted.", indexName);
            }
        }

        catch (HttpRequestException e)
        {
            this._logger.LogError(e, "Deleting index failed: {0}, {1}", e.Message, responseContent);
            throw;
        }

        await this.WaitForIndexStateAsync(indexName, IndexState.Terminating, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task<bool> DoesIndexExistAsync(string indexName, CancellationToken cancel = default)
    {
        this._logger.LogInformation("Checking for index {0}", indexName);
        List<string?>? indexNames = await this.ListIndexesAsync(cancel).ToListAsync(cancel).ConfigureAwait(false);

        if (indexNames.Count == 0 || indexNames == null)
        {
            return false;
        }
        return indexNames.Any(name => name == indexName);
    }

    /// <inheritdoc />
    public async Task<PineconeIndex?> DescribeIndexAsync(string indexName, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Getting Description for Index: {0}", indexName);

        using HttpRequestMessage request = DescribeIndexRequest.Create(indexName).Build();

        request.Headers.Add("accept", "application/json");

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(this.GetIndexOperationsApiBasePath(), request, cancellationToken).ConfigureAwait(false);

        if (response.StatusCode == HttpStatusCode.BadRequest)
        {
            this._logger.LogError("Index Not Found: {0}, {1}", response.StatusCode, responseContent);
            return null;
        }

        try
        {
            response.EnsureSuccessStatusCode();
        }

        catch (HttpRequestException e)
        {
            this._logger.LogError(e, "Describe index failed: {0}, {1}", e.Message, responseContent);
            throw;
        }

        PineconeIndex? indexDescription = JsonSerializer.Deserialize<PineconeIndex>(responseContent, this._jsonSerializerOptions);

        // ensure the indexDescription is not null
        if (indexDescription != null)
        {
            return indexDescription;
        }
        this._logger.LogDebug("Deserialized index description is null");
        return null;
    }

    /// <inheritdoc />
    public async Task ConfigureIndexAsync(string indexName, int replicas = 1, PodType podType = PodType.P1X1, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Configuring index {0}", indexName);

        using HttpRequestMessage request = ConfigureIndexRequest
            .Create(indexName)
            .WithPodType(podType)
            .NumberOfReplicas(replicas)
            .Build();

        request.Headers.Add("accept", "text/plain");

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(this.GetIndexOperationsApiBasePath(), request, cancellationToken).ConfigureAwait(false);

        switch (response.StatusCode)
        {
            // Creation is idempotent, ignore error (and for now ignore vector size)
            case HttpStatusCode.BadRequest:
                this._logger.LogDebug("Request exceeds quota or collection name is invalid. {0}", indexName);
                return;
            case HttpStatusCode.NotFound:
                this._logger.LogDebug("Index not found. {0}", indexName);
                return;
            default:
                try
                {
                    response.EnsureSuccessStatusCode();
                }
                catch (HttpRequestException e)
                {
                    this._logger.LogError(e, "Index configuration failed: {0}, {1}", e.Message, responseContent);
                    throw;
                }

                this._logger.LogDebug("Collection created. {0}", indexName);
                return;
        }
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
    }

    internal async Task<bool> ConnectToHostAsync(string indexName, CancellationToken cancel = default)
    {
        this._logger.LogInformation("Connecting to Pinecone Host");
        PineconeIndex? pineconeIndex = await this.DescribeIndexAsync(indexName, cancel).ConfigureAwait(false);

        if (pineconeIndex == null)
        {
            this._logger.LogError("Index not found");
            return false;
        }

        this._indexDescription = pineconeIndex;
        this._logger.LogInformation("Connected to Pinecone Host {0}", this._indexDescription.Status.Host);
        return true;
    }

    #region private ================================================================================

    private readonly PineconeEnvironment _pineconeEnvironment;
    private readonly ILogger _logger;
    private readonly HttpClient _httpClient;

    private readonly KeyValuePair<string, string> _authHeader;
    private readonly JsonSerializerOptions _jsonSerializerOptions;
    private PineconeIndex? _indexDescription;
    private const int MaxBatchSize = 100;
    private const int PollingInterval = 10;
    private const int Timeout = 5;

    private async Task<string> GetVectorOperationsApiBasePathAsync(string indexName)
    {
        if (this._indexDescription != null && this._indexDescription.Configuration.Name == indexName)
        {
            return $"https://{this._indexDescription!.Status.Host}";
        }

        if (!await this.ConnectToHostAsync(indexName).ConfigureAwait(false) == false)
        {
            this._logger.LogError("Failed to connect to host");
        }

        return $"https://{this._indexDescription!.Status.Host}";
    }

    private string GetIndexOperationsApiBasePath()
    {
        return $"https://controller.{PineconeUtils.EnvironmentToString(this._pineconeEnvironment)}.pinecone.io";
    }

    private async Task WaitForIndexStateAsync(
        string indexName,
        IndexState targetState,
        CancellationToken cancellationToken = default)
    {
        using CancellationTokenSource cts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        TimeSpan timeout = TimeSpan.FromMinutes(Timeout);
        cts.CancelAfter(timeout);

        while (!cts.Token.IsCancellationRequested)
        {
            try
            {
                this._indexDescription = await this.DescribeIndexAsync(indexName, cts.Token).ConfigureAwait(false);
                this._logger.LogInformation("Index {0} is in state {1}", indexName, this._indexDescription?.Status.State);

                if (this._indexDescription?.Status.State == targetState)
                {
                    this._logger.LogInformation("Index {0} reached state {1}. Exiting....", indexName, targetState);
                    break;
                }
            }

            catch (HttpRequestException e)
            {
                this._logger.LogError(e, "Error while polling index state for {0}: {1}", indexName, e.Message);
            }

            await Task.Delay(TimeSpan.FromSeconds(PollingInterval), cts.Token).ConfigureAwait(true);
        }

        if (cts.Token.IsCancellationRequested && !cancellationToken.IsCancellationRequested)
        {
            throw new TimeoutException($"Waiting for index {indexName} to reach state {targetState} timed out after {timeout}.");
        }
    }

    private async Task<(HttpResponseMessage response, string responseContent)> ExecuteHttpRequestAsync(
        string baseURL,
        HttpRequestMessage request,
        CancellationToken cancel = default)
    {
        request.Headers.Add(this._authHeader.Key, this._authHeader.Value);
        request.RequestUri = new Uri(baseURL + request.RequestUri);

        using HttpResponseMessage response = await this._httpClient.SendAsync(request, cancel).ConfigureAwait(false);

        string responseContent = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        
        var logMessage = response.IsSuccessStatusCode ? "Pinecone responded successfully" : "Pinecone responded with error";
        this._logger.LogTrace("{0} - {1}", logMessage, responseContent);

        return (response, responseContent);
    }

    #endregion
}
