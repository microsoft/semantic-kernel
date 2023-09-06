// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using Cloud.Unum.USearch;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Memory.USearch;

public interface IUSearchCollectionStorage : IDisposable
{
    public bool TryGetRecord(string key, out MemoryRecord? memoryRecord, bool withEmbedding);

    public bool Upsert(MemoryRecord record);

    public IEnumerable<string> UpsertBatch(IEnumerable<MemoryRecord> records);

    public void Remove(string key);

    public IEnumerable<(MemoryRecord, double)> GetNearestMatches(
        ReadOnlyMemory<float> embedding,
        int limit,
        double minRelevanceScore = 0.0,
        bool withEmbeddings = false
    );
}

public record class USearchCollectionStorage : IUSearchCollectionStorage
{
    public USearchCollectionStorage(IndexOptions indexOptions)
    {
        this._usearchIndex = new USearchIndex(
            metricKind: indexOptions.metric_kind,
            quantization: indexOptions.quantization,
            dimensions: indexOptions.dimensions,
            connectivity: indexOptions.connectivity,
            expansionAdd: indexOptions.expansion_add,
            expansionSearch: indexOptions.expansion_search,
            multi: indexOptions.multi
        );
    }

    public bool TryGetRecord(string key, out MemoryRecord? memoryRecord, bool withEmbedding)
    {
        if (this._toUSearchKeys.TryGetValue(key, out var usearchKey)
            && this._usearchRecords.TryGetValue(usearchKey, out memoryRecord))
        {
            memoryRecord = withEmbedding
                ? memoryRecord
                : MemoryRecord.FromMetadata(memoryRecord.Metadata, embedding: null, key: memoryRecord.Key, timestamp: memoryRecord.Timestamp);
            return true;
        }
        memoryRecord = null;
        return false;
    }

    public bool Upsert(MemoryRecord record)
    {
        record.Key = record.Metadata.Id;
        if (!this._toUSearchKeys.TryGetValue(record.Key, out ulong usearchKey))
        {
            ulong value = this._nextFreeUSearchKey++;
            this._toUSearchKeys.Add(record.Key, value);
            this._usearchRecords.Add(value, record);
            this._usearchIndex.Add(value, GetOrCreateArray(record.Embedding));
            return true;
        }

        this._usearchRecords[usearchKey] = record;
        this._usearchIndex.Remove(usearchKey);
        this._usearchIndex.Add(usearchKey, GetOrCreateArray(record.Embedding));
        return false;
    }

    // TODO: get around of Roslyn(CA1851)
    public IEnumerable<string> UpsertBatch(IEnumerable<MemoryRecord> records)
    {
        int recordsLen = records.Count();
        float[][] insertVectors = new float[recordsLen][];
        ulong[] usearchKeys = new ulong[recordsLen];
        List<string> insertedKeys = new();

        int nextIndex = 0;
        foreach (var record in records)
        {
            record.Key = record.Metadata.Id;
            float[] embedding = GetOrCreateArray(record.Embedding);
            if (!this._toUSearchKeys.TryGetValue(record.Key, out ulong usearchKey))
            {
                ulong value = this._nextFreeUSearchKey++;
                this._toUSearchKeys.Add(record.Key, value);
                this._usearchRecords.Add(value, record);
            }
            this._usearchRecords[usearchKey] = record;
            this._usearchIndex.Remove(usearchKey);

            insertedKeys.Add(record.Key);
            insertVectors[nextIndex] = GetOrCreateArray(record.Embedding);
        }
        this._usearchIndex.Add(usearchKeys, insertVectors);

        return insertedKeys;
    }

    public void Remove(string key)
    {
        if (!this._toUSearchKeys.TryGetValue(key, out ulong usearchKey))
        {
            return;
        }
        this._toUSearchKeys.Remove(key);
        this._usearchRecords.Remove(usearchKey);
        this._usearchIndex.Remove(usearchKey);
    }

    public IEnumerable<(MemoryRecord, double)> GetNearestMatches(
        ReadOnlyMemory<float> embedding,
        int limit,
        double minRelevanceScore = 0.0,
        bool withEmbeddings = false
    )
    {
        this._usearchIndex.Search(
            queryVector: embedding.ToArray(),
            count: limit,
            out ulong[] usearchKeys,
            out float[] distances
        );

        Func<float, double> distanceToScore = distance => 1 / (double)(distance + 1);
        List<(MemoryRecord, double)> result = new();

        for (int i = 0; i < usearchKeys.Length; i++)
        {
            this._usearchIndex.Get(usearchKeys[i], out float[] vector);
            if (distanceToScore(distances[i]) >= minRelevanceScore && this._usearchRecords.TryGetValue(usearchKeys[i], out MemoryRecord record))
            {
                record = withEmbeddings
                    ? record
                    : MemoryRecord.FromMetadata(record.Metadata, embedding: null, key: record.Key, timestamp: record.Timestamp);

                result.Add((record, (double)distances[i]));
            }
        }

        return result;
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    #region protected ================================================================================

    protected virtual void Dispose(bool disposing)
    {
        if (!this._disposedValue)
        {
            this._usearchIndex.Dispose();
            this._disposedValue = true;
        }
    }

    #endregion

    #region private ================================================================================

    private readonly USearchIndex _usearchIndex;

    private readonly Dictionary<ulong, MemoryRecord> _usearchRecords = new();

    private readonly Dictionary<string, ulong> _toUSearchKeys = new();

    private ulong _nextFreeUSearchKey = 0;

    private bool _disposedValue;

    private static float[] GetOrCreateArray(System.ReadOnlyMemory<float> memory) =>
        MemoryMarshal.TryGetArray(memory, out ArraySegment<float> array) &&
        array.Count == array.Array!.Length ?
            array.Array :
            memory.ToArray();

    #endregion
}
