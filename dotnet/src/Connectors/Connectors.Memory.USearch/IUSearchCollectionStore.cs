// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Memory.USearch;

public interface IUSearchCollectionStore : IDisposable
{
    public bool TryGetRecord(string key, out MemoryRecord? memoryRecord, bool withEmbedding);

    public string Upsert(MemoryRecord record);

    public IEnumerable<string> UpsertBatch(IEnumerable<MemoryRecord> records);

    public void Remove(string key);

    public IEnumerable<(MemoryRecord, double)> GetNearestMatches(
        ReadOnlyMemory<float> embedding,
        int limit,
        double minRelevanceScore = 0.0,
        bool withEmbeddings = false
    );
}
