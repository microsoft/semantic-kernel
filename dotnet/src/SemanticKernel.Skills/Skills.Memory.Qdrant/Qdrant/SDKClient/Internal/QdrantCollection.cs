// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory.Storage;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.Diagnostics;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.Http.Specs;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal;

internal class QdrantCollection : IVectorDbCollection
{
    private readonly ILogger _log;
    private readonly QdrantHttpClientWrapper _vectorHttp;

    public string Name { get; private set; }
    public int VectorSize { get; set; } = 1;
    public string DistanceType { get; set; } = string.Empty;

    public QdrantCollection(string id, QdrantHttpClientWrapper vectorHttp, ILogger log)
    {
        this.Name = id;
        this._vectorHttp = vectorHttp;
        this._log = log ?? NullLogger.Instance;
    }


    public async Task<DataEntry<VectorRecordData<float>>?> GetVectorAsync(string id)
    {
        var point = await this.FindQdrantPointByExternalIdAsync(id);
        if (point == null) { return null; }

        var result = new DataEntry<VectorRecordData<float>>(key: point.ExternalId,
                                               value: new VectorRecordData<float>(
                                                            new Embedding<float>(point.Vector),
                                                            point.ExternalPayload,
                                                            point.ExternalTags));

        return result;
    }

    public async IAsyncEnumerable<DataEntry<VectorRecordData<float>>> GetAllVectorsAsync()
    {
        using HttpRequestMessage vectorRequest = FetchVectorsRequest
            .Fetch(this.Name)
            .Build();

        var (response, responseContent) = await this._vectorHttp.ExecuteHttpRequestAsync(vectorRequest);
        response.EnsureSuccessStatusCode();

        var data = new FetchVectorsResponse(responseContent);
        Verify.Equals("ok", data.Status, $"Something went wrong while getting vectors for {this.Name}");

        foreach (var point in data.VectorPointCollection)
        {
            var record = new DataEntry<VectorRecordData<float>>(key: point.VectorId!,
                                                   value: new VectorRecordData<float>(
                                                                new Embedding<float>(point.Vector!),
                                                                point.Payload!,
                                                                new List<string>()));

            yield return record;
        }
    }

    public Task UpsertVectorAsync(DataEntry<VectorRecordData<float>> record)
    {
        return this.UpsertVectorInternalAsync(record);
    }

    public async Task DeleteVectorAsync(string id)
    {
        var qdrantId = await this.FindQdrantPointIdByExternalIdAsync(id);
        if (qdrantId == null)
        {
            this._log.LogDebug("Nothing to delete, the vector doesn't exist");
            return;
        }

        await this.DeleteVectorInternalAsync(qdrantId);
    }

    public async IAsyncEnumerable<KeyValuePair<DataEntry<VectorRecordData<float>>, double>> FindClosestAsync(float[] target, int top = 1, string[]? requiredTags = null)
    {
        this._log.LogDebug("Searching top {0} closest vectors in {1}", top);

        Verify.NotNull(target, "The given vector is NULL");

        using HttpRequestMessage request = SearchVectorsRequest
            .Create(this.Name)
            .SimilarTo(target)
            .HavingTags(requiredTags)
            .IncludePayLoad()
            .IncludeVectorData()
            .Take(top)
            .Build();

        var (response, responseContent) = await this._vectorHttp.ExecuteHttpRequestAsync(request);
        response.EnsureSuccessStatusCode();

        var data = new SearchVectorsResponse(responseContent);
        Verify.Equals("ok", data.Status, "Something went wrong while looking for the vector");

        if (data.Vectors.Count == 0)
        {
            this._log.LogWarning("Nothing found");
            yield break;
        }

        var result = new List<KeyValuePair<DataEntry<VectorRecordData<float>>, double>>();

        foreach (var v in data.Vectors)
        {
            var record = new DataEntry<VectorRecordData<float>>(key: v.ExternalId,
                                                   value: new VectorRecordData<float>(
                                                                new Embedding<float>(v.Vector),
                                                                v.ExternalPayload,
                                                                v.ExternalTags));

            result.Add(new KeyValuePair<DataEntry<VectorRecordData<float>>, double>(record, v.Score ?? 0));
        }

        // Qdrant search results are currently sorted by id, alphabetically (facepalm)
        result = SortSearchResultByScore(result);
        foreach (var kv in result)
        {
            yield return kv;
        }
    }

    #region private ================================================================================

    private static List<KeyValuePair<DataEntry<VectorRecordData<float>>, double>> SortSearchResultByScore(List<KeyValuePair<DataEntry<VectorRecordData<float>>, double>> list)
    {
        return (from entry in list orderby entry.Value descending select entry).ToList();
    }

    private async Task<string?> FindQdrantPointIdByExternalIdAsync(string externalId)
    {
        var point = await this.FindQdrantPointByExternalIdAsync(externalId);
        return point?.QdrantId;
    }

    private async Task<SearchVectorsResponse.VectorFound?> FindQdrantPointByExternalIdAsync(string externalId)
    {
        this._log.LogDebug("Searching vector by external ID {0}", externalId);

        using HttpRequestMessage request = SearchVectorsRequest
            .Create(this.Name, this.VectorSize)
            .HavingExternalId(externalId)
            .IncludePayLoad()
            .TakeFirst()
            .Build();

        var (response, responseContent) = await this._vectorHttp.ExecuteHttpRequestAsync(request);
        response.EnsureSuccessStatusCode();

        var data = new SearchVectorsResponse(responseContent);
        Verify.Equals("ok", data.Status, "Something went wrong while looking for the vector");

        if (data.Vectors.Count == 0)
        {
            this._log.LogWarning("Vector not found: {0}", externalId);
            return null;
        }

        this._log.LogDebug("Vector {0} found, Qdrant point {1}", externalId, data.Vectors.First().QdrantId);
        return data.Vectors.First();
    }

    private async Task UpsertVectorInternalAsync(DataEntry<VectorRecordData<float>> vector)
    {
        this._log.LogDebug("Upserting vector");
        Verify.NotNull(vector, "The vector is NULL");

        var pointId = string.Empty;

        // See if there's already a vector in Qdrant, querying vectors' payload
        if (!string.IsNullOrEmpty(vector.Key))
        {
            pointId = await this.FindQdrantPointIdByExternalIdAsync(vector.Key);
        }

        // Generate a new ID for the new vector
        if (string.IsNullOrEmpty(pointId))
        {
            pointId = Guid.NewGuid().ToString("D");
        }

        using var request = CreateVectorsRequest.CreateIn(this.Name).UpsertVector(pointId, vector).Build();
        var (response, responseContent) = await this._vectorHttp.ExecuteHttpRequestAsync(request);

        if (response.StatusCode == HttpStatusCode.UnprocessableEntity
            && responseContent.Contains("data did not match any variant of untagged enum ExtendedPointId", StringComparison.OrdinalIgnoreCase))
        {
            throw new VectorDbException("The vector ID must be a GUID string");
        }

        try
        {
            response.EnsureSuccessStatusCode();
        }
        catch (Exception e)
        {
            this._log.LogError(e, "Vector upsert failed: {0}, {1}", e.Message, responseContent);
            throw;
        }
    }

    private async Task DeleteVectorInternalAsync(string qdrantPointId)
    {
        this._log.LogDebug("Deleting vector, point ID {0}", qdrantPointId);

        Verify.NotNullOrEmpty(this.Name, "Collection name is empty");
        Verify.NotNullOrEmpty(qdrantPointId, "Qdrant point ID is empty");

        using var request = DeleteVectorsRequest
            .DeleteFrom(this.Name)
            .DeleteVector(qdrantPointId)
            .Build();
        await this._vectorHttp.ExecuteHttpRequestAsync(request);
    }

    #endregion
}
