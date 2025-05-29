// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Numerics.Tensors;
using Microsoft.SemanticKernel.Memory;

namespace SemanticKernel.IntegrationTests.Connectors.CosmosNoSql;

internal static class DataHelper
{
    public static MemoryRecord[] VectorSearchExpectedResults { get; }
    public static MemoryRecord[] VectorSearchTestRecords { get; }
    public static float[] VectorSearchTestEmbedding { get; }

    static DataHelper()
    {
        VectorSearchTestRecords = CreateBatchRecords(8);
        VectorSearchTestEmbedding = new[] { 1, 0.699f, 0.701f };
        VectorSearchExpectedResults = VectorSearchTestRecords
            .OrderByDescending(r => TensorPrimitives.CosineSimilarity(r.Embedding.Span, VectorSearchTestEmbedding))
            .ToArray();
    }

    public static MemoryRecord[] CreateBatchRecords(int count) =>
        Enumerable
        .Range(0, count)
        .Select(i => MemoryRecord.LocalRecord(
            id: $"test_{i}",
            text: $"text_{i}",
            description: $"description_{i}",
            embedding: new[] { 1, (float)Math.Cos(Math.PI * i / count), (float)Math.Sin(Math.PI * i / count) },
            key: $"test_{i}",
            timestamp: DateTimeOffset.Now))
        .ToArray();
}
