// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.Embeddings;
using Qdrant.DotNet.Internal;
using Qdrant.DotNet.Internal.Diagnostics;
using Qdrant.DotNet.Internal.Http;
using Qdrant.DotNet.Internal.Http.Specs;

namespace Qdrant.DotNet;

public class QdrantDb : IVectorDb
{
    public QdrantDb(
        string endpoint,
        int? port = null,
        HttpClient? httpClient = null,
        ILogger<QdrantDb>? log = null)
    {
        this._log = log.DefaultIfNull();

        this._vectorHttp = new QdrantHttpClientWrapper(
            httpClient ?? new HttpClient(HttpHandlers.CheckCertificateRevocation),
            this._log);
        this._vectorHttp.BaseAddress = endpoint;

        if (port.HasValue)
        {
            this._vectorHttp.AddressPort = port.Value;
        }
    }

    public Task CreateCollectionIfMissing(string collectionName, int vectorSize)
    {
        return this.CreateCollectionInternalAsync(collectionName, vectorSize);
    }

    public async Task<IVectorDbCollection> GetCollectionAsync(string collectionName)
    {
        FetchCollectionResponse? test = await this.FetchCollectionAsync(collectionName);
        if (test == null)
        {
            throw new VectorDbException(VectorDbException.ErrorCodes.CollectionDoesNotExist, nameof(collectionName));
        }

        if (test.Status != "green")
        {
            throw new VectorDbException(VectorDbException.ErrorCodes.InvalidCollectionState,
                $"The vector collection state is not ready: state = {test.Status}");
        }

        return new QdrantCollection(collectionName, this._vectorHttp, this._log)
        {
            VectorSize = test.VectorsSize,
            DistanceType = test.Distance
        };
    }

    public Task DeleteCollection(string collectionName)
    {
        return this.DeleteCollectionInternalAsync(collectionName);
    }

    #region private ================================================================================

    private readonly ILogger<QdrantDb> _log;
    private readonly QdrantHttpClientWrapper _vectorHttp;

    private async Task CreateCollectionInternalAsync(string collectionName, int vectorSize)
    {
        this._log.Debug("Creating collection {0}", collectionName);

        var request = CreateCollectionRequest
            .Create(collectionName)
            .WithVectorSize(vectorSize)
            .WithDistanceType(VectorDistanceType.Cosine)
            .Build();
        var (response, responseContent) = await this._vectorHttp.ExecuteHttpRequestAsync(request);

        // Creation is idempotent, ignore error (and for now ignore vector size)
        if (response.StatusCode == HttpStatusCode.BadRequest)
        {
            if (responseContent.Contains("already exists")) { return; }
        }

        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (Exception e)
        {
            this._log.Error(e, "Collection upsert failed: {0}, {1}", e.Message, responseContent);
            throw;
        }
    }

    private async Task<FetchCollectionResponse?> FetchCollectionAsync(string collectionName)
    {
        this._log.Debug("Fetching collection {0}", collectionName);

        var request = FetchCollectionRequest.Fetch(collectionName).Build();
        var (response, responseContent) = await this._vectorHttp.ExecuteHttpRequestAsync(request);

        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            return null;
        }

        if (response.IsSuccessStatusCode)
        {
            var collection = new FetchCollectionResponse(responseContent);
            return collection;
        }

        this._log.Error("Collection fetch failed: {0}, {1}", response.StatusCode, responseContent);
        throw new VectorDbException($"Unexpected response: {response.StatusCode}");
    }

    private async Task DeleteCollectionInternalAsync(string collectionName)
    {
        this._log.Debug("Deleting collection {0}", collectionName);
        var request = DeleteCollectionRequest.Create(collectionName).Build();
        var (response, responseContent) = await this._vectorHttp.ExecuteHttpRequestAsync(request);
        response.EnsureSuccessStatusCode();
    }

    #endregion
}
