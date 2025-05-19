// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Numerics.Tensors;
using Microsoft.SemanticKernel.Memory;

namespace SemanticKernel.IntegrationTests.Connectors.CosmosMongo;

internal static class DataHelper
{
    public static MemoryRecord[] VectorSearchExpectedResults { get; }
    public static MemoryRecord[] VectorSearchTestRecords { get; }
    public static float[] VectorSearchTestEmbedding { get; }

    static DataHelper()
    {
        VectorSearchTestRecords = CreateBatchRecords(8);
        VectorSearchTestEmbedding = [1, 0.699f, 0.701f];
        VectorSearchExpectedResults = VectorSearchTestRecords
            .OrderByDescending(r => TensorPrimitives.CosineSimilarity(r.Embedding.Span, VectorSearchTestEmbedding))
            .ToArray();
    }

    public static MemoryRecord CreateRecord(string id) =>
        MemoryRecord.LocalRecord(
            id: id,
            text: $"text_{id}",
            description: $"description_{id}",
            embedding: new[] { 1.1f, 2.2f, 3.3f },
            timestamp: GetDateTime());

    public static MemoryRecord[] CreateBatchRecords(int count) =>
        Enumerable
        .Range(0, count)
        .Select(i => MemoryRecord.LocalRecord(
            id: $"test_{i}",
            text: $"text_{i}",
            description: $"description_{i}",
            embedding: new[] { 1, (float)Math.Cos(Math.PI * i / count), (float)Math.Sin(Math.PI * i / count) },
            timestamp: GetDateTime()))
        .ToArray();

    private static DateTime GetDateTime() =>
        new(TimeSpan.TicksPerMillisecond * (DateTime.Now.Ticks / TimeSpan.TicksPerMillisecond), DateTimeKind.Local);
}
