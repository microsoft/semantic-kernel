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

/// <summary>
///  A client for the Pinecone API
/// </summary>
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
        string indexNamespace = "",
        bool includeValues = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this._logger.LogInformation("Searching vectors by id");

        if (!this.Ready)
        {
            this._logger.LogWarning("Index is not ready");
            yield break;
        }

        string basePath = await this.GetVectorOperationsApiBasePathAsync(indexName).ConfigureAwait(false);

        FetchRequest fetchRequest = FetchRequest.FetchVectors(ids)
            .FromNamespace(indexNamespace);

        using HttpRequestMessage request = fetchRequest.Build();

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(basePath, request,
            cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e)
        {
            this._logger.LogError("Error occurred on Get Vectors request: {0}", e.Message);
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

        foreach (PineconeDocument? record in records)
        {
            yield return record;
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<PineconeDocument?> QueryAsync(
        string indexName,
        Query query,
        bool includeValues = false,
        bool includeMetadata = true,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this._logger.LogInformation("Querying top {0} nearest vectors", query.TopK);

        if (!this.Ready)
        {
            this._logger.LogWarning("Index is not ready");
            yield break;
        }

        using HttpRequestMessage request = QueryRequest.QueryIndex(query)
            .WithMetadata(includeMetadata)
            .WithEmbeddings(includeValues)
            .Build();

        string basePath = await this.GetVectorOperationsApiBasePathAsync(indexName).ConfigureAwait(false);

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(basePath, request, cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e)
        {
            this._logger.LogError("Error occurred on Query Vectors request: {0}", e.Message);
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
        string indexNamespace = "",
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

        Query query = Query.Create(topK)
            .WithVector(vector)
            .InNamespace(indexNamespace)
            .WithFilter(filter);

        IAsyncEnumerable<PineconeDocument?> matches = this.QueryAsync(
            indexName, query,
            includeValues,
            includeMetadata, cancellationToken);

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

        // sort documents by score, and order by descending
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
        string indexNamespace = "",
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

            using HttpRequestMessage request = batch.ToNamespace(indexNamespace).Build();

            (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(basePath, request, cancellationToken).ConfigureAwait(false);

            try
            {
                response.EnsureSuccessStatusCode();
            }
            catch (HttpRequestException e)
            {
                this._logger.LogError("Failed to upsert vectors {0}", e.Message);
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
        }

        this._logger.LogInformation("Upserted {0} vectors in {1} batches", totalUpserted, totalBatches);

        return totalUpserted;
    }

    /// <inheritdoc />
    public async Task DeleteAsync(
        string indexName,
        IEnumerable<string>? ids = null,
        string indexNamespace = "",
        Dictionary<string, object>? filter = null,
        bool deleteAll = false,
        CancellationToken cancellationToken = default)
    {
        if (!this.Ready)
        {
            this._logger.LogWarning("Index is not ready");
            return;
        }

        if (ids == null && string.IsNullOrEmpty(indexNamespace) && filter == null && !deleteAll)
        {
            this._logger.LogError("Must provide at least one of ids, filter, or deleteAll");
        }

        ids = ids?.ToList();

        DeleteRequest deleteRequest = deleteAll
            ? string.IsNullOrEmpty(indexNamespace)
                ? DeleteRequest.GetDeleteAllVectorsRequest()
                : DeleteRequest.ClearNamespace(indexNamespace)
            : DeleteRequest.DeleteVectors(ids)
                .FromNamespace(indexNamespace)
                .FilterBy(filter);

        this._logger.LogInformation("Delete operation for Index {0}: {1}", indexName, deleteRequest.ToString());

        string basePath = await this.GetVectorOperationsApiBasePathAsync(indexName).ConfigureAwait(false);

        using HttpRequestMessage request = deleteRequest.Build();

        (HttpResponseMessage response, string _) = await this.ExecuteHttpRequestAsync(basePath, request, cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e)
        {
            this._logger.LogError("Delete operation failed: {0}", e.Message);
        }
    }

    /// <inheritdoc />
    public async Task UpdateAsync(string indexName, PineconeDocument document, string indexNamespace = "", CancellationToken cancellationToken = default)
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
            .InNamespace(indexNamespace)
            .Build();

        (HttpResponseMessage response, string _) = await this.ExecuteHttpRequestAsync(basePath, request, cancellationToken).ConfigureAwait(false);

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

        (HttpResponseMessage _, string responseContent) = await this.ExecuteHttpRequestAsync(this.GetIndexOperationsApiBasePath(), request, cancellationToken).ConfigureAwait(false);

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
        this._logger.LogInformation("Creating index {0}", indexDefinition.ToString());

        string indexName = indexDefinition.Name;

        using HttpRequestMessage request = indexDefinition.Build();

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(this.GetIndexOperationsApiBasePath(), request, cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e) when (response.StatusCode == HttpStatusCode.BadRequest)
        {
            this._logger.LogError(e, "Bad Request: {0}, {1}", response.StatusCode, responseContent);
            throw;
        }
        catch (HttpRequestException e) when (response.StatusCode == HttpStatusCode.Conflict)
        {
            this._logger.LogError(e, "Index of given name already exists: {0}, {1}", response.StatusCode, responseContent);
            throw;
        }
        catch (HttpRequestException e)
        {
            this._logger.LogError(e, "Creating index failed: {0}, {1}", e.Message, responseContent);
            throw;
        }

        this._logger.LogDebug("Index created: {0}, {1}", indexName, responseContent);

        await this.WaitForIndexStateAsync(indexName, IndexState.Ready, cancellationToken).ConfigureAwait(false);

        return this._indexDescription?.Configuration.Name;
    }

    /// <inheritdoc />
    public async Task DeleteIndexAsync(string indexName, CancellationToken cancellationToken = default)
    {
        this._logger.LogInformation("Deleting index {0}", indexName);

        using HttpRequestMessage request = DeleteIndexRequest.Create(indexName).Build();

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
    public async Task<bool> DoesIndexExistAsync(string indexName, CancellationToken cancellationToken = default)
    {
        this._logger.LogInformation("Checking for index {0}", indexName);

        List<string?>? indexNames = await this.ListIndexesAsync(cancellationToken).ToListAsync(cancellationToken).ConfigureAwait(false);

        return indexNames != null && indexNames.Any(name => name == indexName);
    }

    /// <inheritdoc />
    public async Task<PineconeIndex?> DescribeIndexAsync(string indexName, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Getting Description for Index: {0}", indexName);

        using HttpRequestMessage request = DescribeIndexRequest.Create(indexName).Build();

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(this.GetIndexOperationsApiBasePath(), request, cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e) when (response.StatusCode == HttpStatusCode.BadRequest)
        {
            this._logger.LogError(e, "Bad Request: {0}, {1}", response.StatusCode, responseContent);
            throw;
        }
        catch (HttpRequestException e)
        {
            this._logger.LogError(e, "Describe index failed: {0}, {1}", e.Message, responseContent);
            throw;
        }

        PineconeIndex? indexDescription = JsonSerializer.Deserialize<PineconeIndex>(responseContent, this._jsonSerializerOptions);

        if (indexDescription == null)
        {
            this._logger.LogDebug("Deserialized index description is null");
        }

        return indexDescription;
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

        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(this.GetIndexOperationsApiBasePath(), request, cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (HttpRequestException e) when (response.StatusCode == HttpStatusCode.BadRequest)
        {
            this._logger.LogError(e, "Request exceeds quota or collection name is invalid. {0}", indexName);
            throw;
        }
        catch (HttpRequestException e) when (response.StatusCode == HttpStatusCode.NotFound)
        {
            this._logger.LogError(e, "Index not found. {0}", indexName);
            throw;
        }
        catch (HttpRequestException e)
        {
            this._logger.LogError(e, "Index configuration failed: {0}, {1}", e.Message, responseContent);
            throw;
        }

        this._logger.LogDebug("Collection created. {0}", indexName);

        return;
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
    }

    internal async Task<bool> ConnectToHostAsync(string indexName, CancellationToken cancellationToken = default)
    {
        this._logger.LogInformation("Connecting to Pinecone Host");

        PineconeIndex? pineconeIndex = await this.DescribeIndexAsync(indexName, cancellationToken).ConfigureAwait(false);

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
        if (this._indexDescription?.Configuration.Name == indexName)
        {
            return $"https://{this._indexDescription!.Status.Host}";
        }

        if (await this.ConnectToHostAsync(indexName).ConfigureAwait(false))
        {
            return $"https://{this._indexDescription!.Status.Host}";
        }

        this._logger.LogError("Failed to connect to host");

        return string.Empty;

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
        CancellationToken cancellationToken = default)
    {
        request.Headers.Add(this._authHeader.Key, this._authHeader.Value);
        request.RequestUri = new Uri(baseURL + request.RequestUri);

        using HttpResponseMessage response = await this._httpClient.SendAsync(request, cancellationToken).ConfigureAwait(false);

        string responseContent = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

        string logMessage = response.IsSuccessStatusCode ? "Pinecone responded successfully" : "Pinecone responded with error";

        this._logger.LogTrace("{0} - {1}", logMessage, responseContent);

        return (response, responseContent);
    }

    #endregion
}
