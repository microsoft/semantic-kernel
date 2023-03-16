// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory.Storage;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant;

/// <summary>
/// An implementation of a client for the Qdrant VectorDB. This class is used to
/// connect, create, delete, and get embeddings data from a Qdrant VectorDB instance.
/// </summary>
public class QdrantVectorDBClient
{
    public QdrantVectorDBClient(string endpoint, int port)
    {
        this._qdrantDbClient = this.ConnectVectorDB(endpoint, port);
    }

    public async Task<IVectorDbCollection> CreateCollectionAsync(string collectionname, int? vectorsize, string? distancetype)
    {
        IVectorDbCollection collection;
        vectorsize = vectorsize == null ? this._defaultvectorsize : vectorsize.Value;
        distancetype = distancetype == null ? this._defaultdistancetype.ToString() : distancetype;

        try
        {
            await this._qdrantDbClient.CreateCollectionIfMissing(collectionname, vectorsize.Value);
            collection = await this._qdrantDbClient.GetCollectionAsync(collectionname);
        }
        catch (Exception ex)
        {
            throw new Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.Diagnostics.VectorDbException(
                $"Failed to create collection in Qdrant {ex.Message}");
        }

        this._qdrantCollections.TryAdd(collectionname, collection);
        return this._qdrantCollections[collectionname];
    }

    [SuppressMessage("Design", "CA1031:Modify to catch a more specific allowed exception type, or rethrow exception",
        Justification = "Does not throw an exception by design.")]
    public async Task<bool> DeleteCollectionAsync(string collectionname)
    {
        try
        {
            await this._qdrantDbClient.DeleteCollection(collectionname);
            this._qdrantCollections.TryRemove(collectionname, out _);
        }
        catch
        {
            return false;
        }

        return true;
    }

    [SuppressMessage("Design", "CA1031:Modify to catch a more specific allowed exception type, or rethrow exception",
        Justification = "Does not throw an exception by design.")]
    public async Task<bool> DeleteVectorDataAsync(string collectionname, string vectorId)
    {
        IVectorDbCollection? collection = null;

        try
        {
            collection = await this._qdrantDbClient.GetCollectionAsync(collectionname);
            await collection.DeleteVectorAsync(vectorId.ToString());
        }
        catch
        {
            return false;
        }

        this._qdrantCollections[collectionname] = collection;
        return true;
    }

    public async Task<IVectorDbCollection> GetCollectionDataAsync(string collectionKey)
    {
        //var collectionResult = new List<IVectorDbCollection>();
        IVectorDbCollection collection;

        try
        {
            collection = await this._qdrantDbClient.GetCollectionAsync(collectionKey);
        }
        catch (Exception ex)
        {
            throw new Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.Diagnostics.VectorDbException(
                $"Failed to get collections from Qdrant, {ex.Message}");
        }

        return collection;
    }

    public async Task<IAsyncEnumerable<DataEntry<VectorRecordData<float>>>> GetVectorsByCollection(string collectionname)
    {
        IVectorDbCollection collection;
        IAsyncEnumerable<DataEntry<VectorRecordData<float>>>? vectors = null;
        try
        {
            collection = await this._qdrantDbClient.GetCollectionAsync(collectionname);
            vectors = collection.GetAllVectorsAsync();
        }
        catch
        {
            throw new Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.Diagnostics.VectorDbException(
                $"Failed to get vectors by collection from Qdrant");
        }

        return vectors!;
    }

    public async Task<DataEntry<VectorRecordData<float>>> GetVectorDataAsync(string collectionname, string vectorId)
    {
        IVectorDbCollection collection;
        DataEntry<VectorRecordData<float>> result;

        try
        {
            collection = await this._qdrantDbClient.GetCollectionAsync(collectionname);
            var record = await collection.GetVectorAsync(vectorId);
            result = record != null ? (DataEntry<VectorRecordData<float>>)record : new DataEntry<VectorRecordData<float>>();
        }
        catch (Exception ex) //look up specific exece
        {
            throw new Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.Diagnostics.VectorDbException(
                $"Failed to get vector from Qdrant, {ex.Message}");
        }

        return result;
    }

    [SuppressMessage("Design", "CA1031:Modify to catch a more specific allowed exception type, or rethrow exception",
        Justification = "Does not throw an exception by design.")]
    public async Task<bool> PutVectorDataAsync<TVector>(string collectionname, string vectorId, TVector vectordata, Dictionary<string, object>? metadata)
    {
        IVectorDbCollection collection;
        Dictionary<string, object> _metadata = new Dictionary<string, object>();
        var vector = vectordata as float[];

        if (vectordata == null)
        {
            throw new ArgumentNullException(nameof(vectordata));
        }

        _metadata = metadata == null ? _metadata : metadata;

        DataEntry<VectorRecordData<float>> vectorRecord =
            new DataEntry<VectorRecordData<float>>(key: vectorId,
                value: new VectorRecordData<float>(
                    new Embedding<float>(vector!),
                    _metadata,
                    new List<string>()));

        try
        {
            collection = await this._qdrantDbClient.GetCollectionAsync(collectionname);
            await collection.UpsertVectorAsync(vectorRecord);
            this._qdrantCollections[collectionname] = collection;
        }
        catch
        {
            return false;
        }

        return true;
    }

    public async Task<IEnumerable<KeyValuePair<DataEntry<VectorRecordData<float>>, double>>> SearchVectorBySimilarityAsync(string collectionname,
        DataEntry<VectorRecordData<float>> recordData, double minScore)
    {
        List<KeyValuePair<DataEntry<VectorRecordData<float>>, double>> matchresults = new List<KeyValuePair<DataEntry<VectorRecordData<float>>, double>>();
        List<KeyValuePair<DataEntry<VectorRecordData<float>>, double>> vectorresults;
        try
        {
            IVectorDbCollection collection = await this._qdrantDbClient.GetCollectionAsync(collectionname);
            vectorresults = await collection.FindClosestAsync(recordData).ToListAsync();

            if (vectorresults != null && vectorresults.Count > 0)
            {
                foreach (var match in vectorresults)
                {
                    if (match.Value >= minScore)
                    {
                        matchresults.Add(new KeyValuePair<DataEntry<VectorRecordData<float>>, double>(match.Key, match.Value));
                    }
                }
            }
        }
        catch (Exception ex)
        {
            throw new Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.Diagnostics.VectorDbException(
                $"Error occurred, Failed to get nearest matches from Qdrant{ex.Message}");
        }

        return matchresults;
    }

    public QdrantDb ConnectVectorDB(string hostendpoint, int port)
    {
        var client = new QdrantDb(hostendpoint, port);
        return client;
    }

    #region private ================================================================================

    private readonly ConcurrentDictionary<string, IVectorDbCollection> _qdrantCollections = new();
    private QdrantDb _qdrantDbClient;
    private readonly int _defaultvectorsize = 1536; //output dimension size for OpenAI's text-emebdding-ada-002
    private readonly VectorDistanceType _defaultdistancetype = VectorDistanceType.Cosine;

    #endregion
}
