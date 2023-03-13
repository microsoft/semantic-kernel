// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory.Storage;
using Qdrant.DotNet;


namespace Microsoft.SemanticKernel.Skills.Memory.VectorDB;

/// <summary>
/// An implementation of a client for the Qdrant VectorDB. This class is used to 
/// connect, create, delete, and get embeddings data from a Qdrant VectorDB instance.
/// </summary>

public class QdrantVectorDb
{
    public QdrantVectorDb(string endpoint, int port)
    {

        this._qdrantdbclient = this.ConnectVectorDB(endpoint, port);

    }

    public async Task<IVectorDbCollection> CreateCollectionAsync(string collectionname, int? vectorsize, string? distancetype)
    {
        IVectorDbCollection collection;
        vectorsize = vectorsize == null ? this._defaultvectorsize : vectorsize.Value;
        distancetype = distancetype == null ? this._defaultdistancetype.ToString() : distancetype;

        try
        {
            await this._qdrantdbclient.CreateCollectionIfMissing(collectionname, vectorsize.Value);
            collection = await this._qdrantdbclient.GetCollectionAsync(collectionname);
        }
        catch (Exception ex)
        {
            throw new Qdrant.DotNet.Internal.Diagnostics.VectorDbException($"Failed to create collection in Qdrant {ex.Message}");
        }

        this._qdrantcollections.TryAdd(collectionname, collection);
        return this._qdrantcollections[collectionname];
    }


    public async Task<bool> DeleteCollectionAsync(string collectionname)
    {
        try
        {
            await this._qdrantdbclient.DeleteCollection(collectionname);
            this._qdrantcollections.TryRemove(collectionname, out _);
        }
        catch
        {
            return false;
        }

        return true;
    }

    public async Task<bool> DeleteVectorDataAsync(string collectionname, string vectorid)
    {
        IVectorDbCollection? collection = null;

        try
        {
            collection = await this._qdrantdbclient.GetCollectionAsync(collectionname);
            await collection.DeleteVectorAsync(vectorid.ToString());
        }
        catch
        {
            return false;
        }

        this._qdrantcollections[collectionname] = collection;
        return true;

    }

    public async Task<IVectorDbCollection> GetCollectionDataAsync(string collectionkey)
    {
        //var collectionResult = new List<IVectorDbCollection>();
        IVectorDbCollection collection;

        try
        {
            collection = await this._qdrantdbclient.GetCollectionAsync(collectionkey);
        }
        catch (Exception ex)
        {
            throw new Qdrant.DotNet.Internal.Diagnostics.VectorDbException($"Failed to get collections from Qdrant, {ex.Message}");
        }

        return collection;
    }

    public async Task<IAsyncEnumerable<DataEntry<VectorRecordData<float>>>> GetVectorsByCollection(string collectionname)
    {
        IVectorDbCollection collection;
        IAsyncEnumerable<DataEntry<VectorRecordData<float>>>? vectors = null;
        try
        {
            collection = await this._qdrantdbclient.GetCollectionAsync(collectionname);
            vectors = collection.GetAllVectorsAsync();
        }
        catch
        {
            throw new Qdrant.DotNet.Internal.Diagnostics.VectorDbException($"Failed to get vectors by collection from Qdrant");
        }

        return vectors!;

    }

    public async Task<DataEntry<VectorRecordData<float>>> GetVectorDataAsync(string collectionname, string vectorid)
    {
        IVectorDbCollection collection;
        DataEntry<VectorRecordData<float>> result;

        try
        {
            collection = await this._qdrantdbclient.GetCollectionAsync(collectionname);
            var record = await collection.GetVectorAsync(vectorid);
            result = record != null ?
                        (DataEntry<VectorRecordData<float>>)record :
                        new DataEntry<VectorRecordData<float>>();
        }
        catch (Exception ex) //look up specific exece
        {
            throw new Qdrant.DotNet.Internal.Diagnostics.VectorDbException($"Failed to get vector from Qdrant, {ex.Message}");
        }

        return result;
    }

    public async Task<bool> PutVectorDataAsync<TVector>(string collectionname, string vectorid, TVector vectordata, Dictionary<string, object>? metadata)
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
            new DataEntry<VectorRecordData<float>>(key: vectorid,
                                                        value: new VectorRecordData<float>(
                                                            new Embedding<float>(vector!),
                                                            _metadata,
                                                            new List<string>()));

        try
        {
            collection = await this._qdrantdbclient.GetCollectionAsync(collectionname);
            await collection.UpsertVectorAsync(vectorRecord);
            this._qdrantcollections[collectionname] = collection;
        }
        catch
        {
            return false;
        }

        return true;

    }

    public async Task<IEnumerable<KeyValuePair<DataEntry<VectorRecordData<float>>, double>>> SearchVectorBySimilarityAsync(string collectionname, DataEntry<VectorRecordData<float>> recordData, double minScore)
    {
        List<KeyValuePair<DataEntry<VectorRecordData<float>>, double>> matchresults = new List<KeyValuePair<DataEntry<VectorRecordData<float>>, double>>();
        List<KeyValuePair<DataEntry<VectorRecordData<float>>, double>> vectorresults;
        try
        {
            IVectorDbCollection collection = await this._qdrantdbclient.GetCollectionAsync(collectionname);
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
            throw new Qdrant.DotNet.Internal.Diagnostics.VectorDbException($"Error occurred, Failed to get nearest matches from Qdrant{ex.Message}");
        }

        return matchresults;

    }

    public QdrantDb ConnectVectorDB(string hostendpoint, int port)
    {
        var client = new QdrantDb(hostendpoint, port);
        return client;
    }

    #region private ================================================================================
    private readonly ConcurrentDictionary<string, IVectorDbCollection> _qdrantcollections = new();
    private QdrantDb _qdrantdbclient;
    private readonly int _defaultvectorsize = 1536; //output dimension size for OpenAI's text-emebdding-ada-002
    private readonly VectorDistanceType _defaultdistancetype = VectorDistanceType.Cosine;

    #endregion


}
