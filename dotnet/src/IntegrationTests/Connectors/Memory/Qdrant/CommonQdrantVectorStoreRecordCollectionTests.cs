// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Qdrant;

/// <summary>
/// Inherits common integration tests that should pass for any <see cref="VectorStoreCollection{TKey, TRecord}"/>.
/// </summary>
/// <param name="fixture">Qdrant setup and teardown.</param>
[Collection("QdrantVectorStoreCollection")]
public class CommonQdrantVectorStoreRecordCollectionTests(QdrantVectorStoreFixture fixture) : BaseVectorStoreRecordCollectionTests<ulong>
{
    protected override ulong Key1 => 1;
    protected override ulong Key2 => 2;
    protected override ulong Key3 => 3;
    protected override ulong Key4 => 4;

    protected override VectorStoreCollection<ulong, TRecord> GetTargetRecordCollection<TRecord>(string recordCollectionName, VectorStoreCollectionDefinition? definition)
    {
        return new QdrantCollection<ulong, TRecord>(fixture.QdrantClient, recordCollectionName, ownsClient: false, new()
        {
            HasNamedVectors = true,
            Definition = definition
        });
    }

    protected override HashSet<string> GetSupportedDistanceFunctions()
    {
        return [DistanceFunction.CosineSimilarity, DistanceFunction.EuclideanDistance, DistanceFunction.ManhattanDistance];
    }
}
