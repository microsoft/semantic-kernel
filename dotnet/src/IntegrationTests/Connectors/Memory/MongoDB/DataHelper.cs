// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;
using Microsoft.SemanticKernel.Memory;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.MongoDB;

internal static class DataHelper
{
    public static MemoryRecord[] VectorSearchTestRecords { get; }
    public static float[] VectorSearchTestEmbedding { get; }
    public static MemoryRecord[] VectorSearchExpectedResults { get; }

    static DataHelper()
    {
        VectorSearchTestRecords = CreateBatchRecords(8);
        VectorSearchTestEmbedding = new[] { 1, 0.7f, 0.7f };
        VectorSearchExpectedResults = VectorSearchTestRecords
            .OrderByDescending(r => r.Embedding.Span.CosineSimilarity(VectorSearchTestEmbedding))
            .ToArray();
    }

    public static MemoryRecord CreateRecord(string id) =>
        MemoryRecord.LocalRecord(
            id: id,
            text: $"text_{id}",
            description: $"description_{id}",
            embedding: new[] { 1.1f, 2.2f, 3.3f });

    public static MemoryRecord[] CreateBatchRecords(int count) =>
        Enumerable
        .Range(0, count)
        .Select(i => MemoryRecord.LocalRecord(
            id: $"test_{i}",
            text: $"text_{i}",
            description: $"description_{i}",
            embedding: new[] { 1, (float)Math.Cos(Math.PI * i / count), (float)Math.Sin(Math.PI * i / count) }))
        .ToArray();
}
