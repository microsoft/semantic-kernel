<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> origin/main
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes

using System;
using System.Collections.Concurrent;
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
using Microsoft.SemanticKernel.Http;
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;
using Microsoft.SemanticKernel.Diagnostics;
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;
using Microsoft.SemanticKernel.Diagnostics;
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// A client for the Pinecone API
/// </summary>
public sealed class PineconeClient : IPineconeClient
{
    /// <summary>
    /// Initializes a new instance of the <see cref="PineconeClient"/> class.
    /// </summary>
    /// <param name="pineconeEnvironment">The environment for Pinecone.</param>
    /// <param name="apiKey">The API key for accessing Pinecone services.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="httpClient">An optional HttpClient instance for making HTTP requests.</param>
    public PineconeClient(string pineconeEnvironment, string apiKey, ILoggerFactory? loggerFactory = null, HttpClient? httpClient = null)
    {
        this._pineconeEnvironment = pineconeEnvironment;
        this._authHeader = new KeyValuePair<string, string>("Api-Key", apiKey);
        this._jsonSerializerOptions = PineconeUtils.DefaultSerializerOptions;
        this._logger = loggerFactory?.CreateLogger(typeof(PineconeClient)) ?? NullLogger.Instance;
        this._httpClient = HttpClientProvider.GetHttpClient(httpClient);
        this._indexHostMapping = new ConcurrentDictionary<string, string>();
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<PineconeDocument?> FetchVectorsAsync(
        string indexName,
        IEnumerable<string> ids,
        string indexNamespace = "",
        bool includeValues = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Searching vectors by id");

        string basePath = await this.GetVectorOperationsApiBasePathAsync(indexName).ConfigureAwait(false);

        FetchRequest fetchRequest = FetchRequest.FetchVectors(ids)
            .FromNamespace(indexNamespace);

        using HttpRequestMessage request = fetchRequest.Build();

        string? responseContent = null;

        try
        {
            (_, responseContent) = await this.ExecuteHttpRequestAsync(basePath, request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Error occurred on Get Vectors request: {Message}", e.Message);
            yield break;
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError("Error occurred on Get Vectors request: {0}", e.Message);
            throw;
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        }

        FetchResponse? data = JsonSerializer.Deserialize<FetchResponse>(responseContent, this._jsonSerializerOptions);

        if (data is null)
        {
            this._logger.LogWarning("Unable to deserialize Get response");
            yield break;
        }

        if (data.Vectors.Count == 0)
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
        this._logger.LogDebug("Querying top {0} nearest vectors", query.TopK);

        using HttpRequestMessage request = QueryRequest.QueryIndex(query)
            .WithMetadata(includeMetadata)
            .WithEmbeddings(includeValues)
            .Build();

        string basePath = await this.GetVectorOperationsApiBasePathAsync(indexName).ConfigureAwait(false);

        string? responseContent = null;

        try
        {
            (_, responseContent) = await this.ExecuteHttpRequestAsync(basePath, request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Error occurred on Query Vectors request: {Message}", e.Message);
            yield break;
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError("Error occurred on Query Vectors request: {0}", e.Message);
            throw;
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        }

        QueryResponse? queryResponse = JsonSerializer.Deserialize<QueryResponse>(responseContent, this._jsonSerializerOptions);

        if (queryResponse is null)
        {
            this._logger.LogWarning("Unable to deserialize Query response");
            yield break;
        }

        if (queryResponse.Matches.Count == 0)
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
        ReadOnlyMemory<float> vector,
        double threshold,
        int topK,
        bool includeValues,
        bool includeMetadata,
        string indexNamespace = "",
        Dictionary<string, object>? filter = default,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Searching top {0} nearest vectors with threshold {1}", topK, threshold);

        List<(PineconeDocument document, float score)> documents = [];

        Query query = Query.Create(topK)
            .WithVector(vector)
            .InNamespace(indexNamespace)
            .WithFilter(filter);

        IAsyncEnumerable<PineconeDocument?> matches = this.QueryAsync(
            indexName, query,
            includeValues,
            includeMetadata, cancellationToken);

        await foreach (PineconeDocument? match in matches.WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            if (match is null)
            {
                continue;
            }

            if (match.Score > threshold)
            {
                documents.Add((match, match.Score ?? 0));
            }
        }

        if (documents.Count == 0)
        {
            this._logger.LogWarning("No relevant documents found");
            yield break;
        }

        // sort documents descending by score
        documents.Sort((x, y) => y.score.CompareTo(x.score));

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
        this._logger.LogDebug("Upserting vectors");

        int totalUpserted = 0;
        int totalBatches = 0;

        string basePath = await this.GetVectorOperationsApiBasePathAsync(indexName).ConfigureAwait(false);
        IAsyncEnumerable<PineconeDocument> validVectors = PineconeUtils.EnsureValidMetadataAsync(vectors.ToAsyncEnumerable());

        await foreach (UpsertRequest? batch in PineconeUtils.GetUpsertBatchesAsync(validVectors, MaxBatchSize).WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            totalBatches++;

            using HttpRequestMessage request = batch.ToNamespace(indexNamespace).Build();

            string? responseContent = null;

            try
            {
                (_, responseContent) = await this.ExecuteHttpRequestAsync(basePath, request, cancellationToken).ConfigureAwait(false);
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
                response.EnsureSuccess(responseContent, this._logger);
>>>>>>> Stashed changes
=======
                response.EnsureSuccess(responseContent, this._logger);
>>>>>>> Stashed changes
=======
                response.EnsureSuccess(responseContent, this._logger);
>>>>>>> Stashed changes
=======
                response.EnsureSuccess(responseContent, this._logger);
>>>>>>> Stashed changes
=======
                response.EnsureSuccess(responseContent, this._logger);
>>>>>>> Stashed changes
=======
                response.EnsureSuccess(responseContent, this._logger);
>>>>>>> origin/main
=======
                response.EnsureSuccess(responseContent, this._logger);
>>>>>>> Stashed changes
            }
            catch (HttpOperationException e)
            {
                this._logger.LogError(e, "Failed to upsert vectors {Message}", e.Message);
                throw;
            }

            UpsertResponse? data = JsonSerializer.Deserialize<UpsertResponse>(responseContent, this._jsonSerializerOptions);

            if (data is null)
            {
                this._logger.LogWarning("Unable to deserialize Upsert response");
                continue;
            }

            totalUpserted += data.UpsertedCount;

            this._logger.LogDebug("Upserted batch {0} with {1} vectors", totalBatches, data.UpsertedCount);
        }

        this._logger.LogDebug("Upserted {0} vectors in {1} batches", totalUpserted, totalBatches);

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
        if (ids is null && string.IsNullOrEmpty(indexNamespace) && filter is null && !deleteAll)
        {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            throw new ArgumentException("Must provide at least one of ids, filter, or deleteAll");
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
            throw new ArgumentException("Must provide at least one of ids, filter, or deleteAll");
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
            throw new ArgumentException("Must provide at least one of ids, filter, or deleteAll");
=======
>>>>>>> Stashed changes
<<<<<<< main
<<<<<<< main
            throw new ArgumentException("Must provide at least one of ids, filter, or deleteAll");
=======
            throw new SKException("Must provide at least one of ids, filter, or deleteAll");
>>>>>>> ms/feature-error-handling
=======
            throw new SKException("Must provide at least one of ids, filter, or deleteAll");
>>>>>>> ms/feature-error-handling-part3
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
        }

        ids = ids?.ToList();

        DeleteRequest deleteRequest = deleteAll
            ? string.IsNullOrEmpty(indexNamespace)
                ? DeleteRequest.GetDeleteAllVectorsRequest()
                : DeleteRequest.ClearNamespace(indexNamespace)
            : DeleteRequest.DeleteVectors(ids)
                .FromNamespace(indexNamespace)
                .FilterBy(filter);

        this._logger.LogDebug("Delete operation for Index {0}: {1}", indexName, deleteRequest.ToString());

        string basePath = await this.GetVectorOperationsApiBasePathAsync(indexName).ConfigureAwait(false);

        using HttpRequestMessage request = deleteRequest.Build();

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        try
        {
            await this.ExecuteHttpRequestAsync(basePath, request, cancellationToken).ConfigureAwait(false);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
<<<<<<< main
        try
        {
            await this.ExecuteHttpRequestAsync(basePath, request, cancellationToken).ConfigureAwait(false);
=======
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(basePath, request, cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccess(responseContent, this._logger);
>>>>>>> ms/feature-error-handling
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Delete operation failed: {Message}", e.Message);
            throw;
        }
    }

    /// <inheritdoc />
    public async Task UpdateAsync(string indexName, PineconeDocument document, string indexNamespace = "", CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Updating vector: {0}", document.Id);

        string basePath = await this.GetVectorOperationsApiBasePathAsync(indexName).ConfigureAwait(false);

        using HttpRequestMessage request = UpdateVectorRequest
            .FromPineconeDocument(document)
            .InNamespace(indexNamespace)
            .Build();

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
        try
        {
            await this.ExecuteHttpRequestAsync(basePath, request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Vector update for Document {Id} failed. {Message}", document.Id, e.Message);
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(basePath, request, cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Vector update for Document {0} failed. Message: {1}", document.Id, e.Message);
>>>>>>> ms/feature-error-handling
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
            throw;
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

        string? responseContent = null;

        try
        {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
            (_, responseContent) = await this.ExecuteHttpRequestAsync(basePath, request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Index not found {Message}", e.Message);
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Index not found {0}", e.Message);
>>>>>>> ms/feature-error-handling
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
            throw;
        }

        IndexStats? result = JsonSerializer.Deserialize<IndexStats>(responseContent, this._jsonSerializerOptions);

        if (result is not null)
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

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        (HttpResponseMessage _, string responseContent) = await this.ExecuteHttpRequestAsync(this.GetIndexOperationsApiBasePath(), request, cancellationToken).ConfigureAwait(false);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(this.GetIndexOperationsApiBasePath(), request, cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Listing index names failed. Message: {0}", e.Message);
            throw;
        }
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

        string[]? indices = JsonSerializer.Deserialize<string[]?>(responseContent, this._jsonSerializerOptions);

        if (indices is null)
        {
            yield break;
        }

        foreach (string? index in indices)
        {
            yield return index;
        }
    }

    /// <inheritdoc />
    public async Task CreateIndexAsync(IndexDefinition indexDefinition, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Creating index {0}", indexDefinition.ToString());

        string indexName = indexDefinition.Name;

        using HttpRequestMessage request = indexDefinition.Build();

        try
        {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
            await this.ExecuteHttpRequestAsync(this.GetIndexOperationsApiBasePath(), request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e) when (e.StatusCode == HttpStatusCode.BadRequest)
        {
            this._logger.LogError(e, "Bad Request: {StatusCode}, {Response}", e.StatusCode, e.ResponseContent);
            throw;
        }
        catch (HttpOperationException e) when (e.StatusCode == HttpStatusCode.Conflict)
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e) when (response.StatusCode == HttpStatusCode.Conflict)
>>>>>>> ms/feature-error-handling
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        {
            this._logger.LogError(e, "Index of given name already exists: {StatusCode}, {Response}", e.StatusCode, e.ResponseContent);
            throw;
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Creating index failed: {Message}, {Response}", e.Message, e.ResponseContent);
            throw;
        }
    }

    /// <inheritdoc />
    public async Task DeleteIndexAsync(string indexName, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Deleting index {0}", indexName);

        using HttpRequestMessage request = DeleteIndexRequest.Create(indexName).Build();

        try
        {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            await this.ExecuteHttpRequestAsync(this.GetIndexOperationsApiBasePath(), request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e) when (e.StatusCode == HttpStatusCode.NotFound)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
<<<<<<< main
            await this.ExecuteHttpRequestAsync(this.GetIndexOperationsApiBasePath(), request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e) when (e.StatusCode == HttpStatusCode.NotFound)
=======
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e) when (response.StatusCode == HttpStatusCode.NotFound)
>>>>>>> ms/feature-error-handling
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        {
            this._logger.LogError(e, "Index Not Found: {StatusCode}, {Response}", e.StatusCode, e.ResponseContent);
            throw;
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Deleting index failed: {Message}, {Response}", e.Message, e.ResponseContent);
            throw;
        }

        this._logger.LogDebug("Index: {0} has been successfully deleted.", indexName);
    }

    /// <inheritdoc />
    public async Task<bool> DoesIndexExistAsync(string indexName, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Checking for index {0}", indexName);

        List<string?>? indexNames = await this.ListIndexesAsync(cancellationToken).ToListAsync(cancellationToken).ConfigureAwait(false);

        if (indexNames is null || !indexNames.Any(name => name == indexName))
        {
            return false;
        }

        PineconeIndex? index = await this.DescribeIndexAsync(indexName, cancellationToken).ConfigureAwait(false);

        return index is not null && index.Status.State == IndexState.Ready;
    }

    /// <inheritdoc />
    public async Task<PineconeIndex?> DescribeIndexAsync(string indexName, CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Getting Description for Index: {0}", indexName);

        using HttpRequestMessage request = DescribeIndexRequest.Create(indexName).Build();

        string? responseContent = null;

        try
        {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
            (_, responseContent) = await this.ExecuteHttpRequestAsync(this.GetIndexOperationsApiBasePath(), request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e) when (e.StatusCode == HttpStatusCode.BadRequest)
        {
            this._logger.LogError(e, "Bad Request: {StatusCode}, {Response}", e.StatusCode, e.ResponseContent);
            throw;
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
            response.EnsureSuccess(responseContent, this._logger);
>>>>>>> ms/feature-error-handling
>>>>>>> Stashed changes
=======
=======
            response.EnsureSuccess(responseContent, this._logger);
>>>>>>> ms/feature-error-handling
>>>>>>> Stashed changes
=======
=======
            response.EnsureSuccess(responseContent, this._logger);
>>>>>>> ms/feature-error-handling
>>>>>>> Stashed changes
=======
=======
            response.EnsureSuccess(responseContent, this._logger);
>>>>>>> ms/feature-error-handling
>>>>>>> Stashed changes
=======
=======
            response.EnsureSuccess(responseContent, this._logger);
>>>>>>> ms/feature-error-handling
>>>>>>> Stashed changes
=======
=======
            response.EnsureSuccess(responseContent, this._logger);
>>>>>>> ms/feature-error-handling
>>>>>>> origin/main
=======
=======
            response.EnsureSuccess(responseContent, this._logger);
>>>>>>> ms/feature-error-handling
>>>>>>> Stashed changes
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Describe index failed: {Message}, {Response}", e.Message, e.ResponseContent);
            throw;
        }

        PineconeIndex? indexDescription = JsonSerializer.Deserialize<PineconeIndex>(responseContent, this._jsonSerializerOptions);

        if (indexDescription is null)
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

        try
        {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
            await this.ExecuteHttpRequestAsync(this.GetIndexOperationsApiBasePath(), request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e) when (e.StatusCode == HttpStatusCode.BadRequest)
=======
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
            await this.ExecuteHttpRequestAsync(this.GetIndexOperationsApiBasePath(), request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e) when (e.StatusCode == HttpStatusCode.BadRequest)
=======
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e) when (response.StatusCode == HttpStatusCode.BadRequest)
>>>>>>> ms/feature-error-handling
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        {
            this._logger.LogError(e, "Request exceeds quota or collection name is invalid. {Index}", indexName);
            throw;
        }
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        catch (HttpOperationException e) when (e.StatusCode == HttpStatusCode.NotFound)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        catch (HttpOperationException e) when (e.StatusCode == HttpStatusCode.NotFound)
=======
        catch (HttpOperationException e) when (response.StatusCode == HttpStatusCode.NotFound)
>>>>>>> ms/feature-error-handling
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
        catch (HttpOperationException e) when (e.StatusCode == HttpStatusCode.NotFound)
=======
        catch (HttpOperationException e) when (response.StatusCode == HttpStatusCode.NotFound)
>>>>>>> ms/feature-error-handling
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        {
            this._logger.LogError(e, "Index not found. {Index}", indexName);
            throw;
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Index configuration failed: {Message}, {Response}", e.Message, e.ResponseContent);
            throw;
        }

        this._logger.LogDebug("Collection created. {0}", indexName);
    }

    #region private ================================================================================

    private readonly string _pineconeEnvironment;
    private readonly ILogger _logger;
    private readonly HttpClient _httpClient;

    private readonly KeyValuePair<string, string> _authHeader;
    private readonly JsonSerializerOptions _jsonSerializerOptions;
    private readonly ConcurrentDictionary<string, string> _indexHostMapping;
    private const int MaxBatchSize = 100;

    private async Task<string> GetVectorOperationsApiBasePathAsync(string indexName)
    {
        string indexHost = await this.GetIndexHostAsync(indexName).ConfigureAwait(false);

        return $"https://{indexHost}";
    }

    private string GetIndexOperationsApiBasePath()
    {
        return $"https://controller.{this._pineconeEnvironment}.pinecone.io";
    }

    private async Task<(HttpResponseMessage response, string responseContent)> ExecuteHttpRequestAsync(
        string baseURL,
        HttpRequestMessage request,
        CancellationToken cancellationToken = default)
    {
        request.Headers.Add(this._authHeader.Key, this._authHeader.Value);
        request.RequestUri = new Uri(baseURL + request.RequestUri);

        using HttpResponseMessage response = await this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);

        string responseContent = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        return (response, responseContent);
    }

    private async Task<string> GetIndexHostAsync(string indexName, CancellationToken cancellationToken = default)
    {
        if (this._indexHostMapping.TryGetValue(indexName, out string? indexHost))
        {
            return indexHost;
        }

        this._logger.LogDebug("Getting index host from Pinecone.");

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        PineconeIndex pineconeIndex = await this.DescribeIndexAsync(indexName, cancellationToken).ConfigureAwait(false) ??
            throw new KernelException("Index not found in Pinecone. Create index to perform operations with vectors.");
=======
<<<<<<< main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        PineconeIndex pineconeIndex = await this.DescribeIndexAsync(indexName, cancellationToken).ConfigureAwait(false) ??
            throw new KernelException("Index not found in Pinecone. Create index to perform operations with vectors.");

        if (string.IsNullOrWhiteSpace(pineconeIndex.Status.Host))
        {
            throw new KernelException($"Host of index {indexName} is unknown.");
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
        PineconeIndex? pineconeIndex = await this.DescribeIndexAsync(indexName, cancellationToken).ConfigureAwait(false);

        if (pineconeIndex == null)
        {
            throw new SKException("Index not found in Pinecone. Create index to perform operations with vectors.");
        }
>>>>>>> origin/main

        if (string.IsNullOrWhiteSpace(pineconeIndex.Status.Host))
        {
            throw new SKException($"Host of index {indexName} is unknown.");
<<<<<<< main
>>>>>>> ms/feature-error-handling
=======
>>>>>>> ms/feature-error-handling-part3
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        }

        this._logger.LogDebug("Found host {0} for index {1}", pineconeIndex.Status.Host, indexName);

        this._indexHostMapping.TryAdd(indexName, pineconeIndex.Status.Host);

        return pineconeIndex.Status.Host;
    }

    #endregion
}
