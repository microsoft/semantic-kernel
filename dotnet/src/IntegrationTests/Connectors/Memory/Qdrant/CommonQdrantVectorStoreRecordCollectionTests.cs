// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Qdrant;

/// <summary>
/// Inherits common integration tests that should pass for any <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.
/// </summary>
/// <param name="fixture">Qdrant setup and teardown.</param>
[Collection("QdrantVectorStoreCollection")]
public class CommonQdrantVectorStoreRecordCollectionTests(QdrantVectorStoreFixture fixture) : BaseVectorStoreRecordCollectionTests<ulong>
{
    protected override ulong Key1 => 1;
    protected override ulong Key2 => 2;
    protected override ulong Key3 => 3;
    protected override ulong Key4 => 4;

    protected override IVectorStoreRecordCollection<ulong, TRecord> GetTargetRecordCollection<TRecord>(string recordCollectionName, VectorStoreRecordDefinition? vectorStoreRecordDefinition)
    {
        return new QdrantVectorStoreRecordCollection<ulong, TRecord>(fixture.QdrantClient, recordCollectionName, new()
        {
            HasNamedVectors = true,
            VectorStoreRecordDefinition = vectorStoreRecordDefinition
        });
    }

    protected override HashSet<string> GetSupportedDistanceFunctions()
    {
        return [DistanceFunction.CosineSimilarity, DistanceFunction.EuclideanDistance, DistanceFunction.ManhattanDistance];
    }
}
