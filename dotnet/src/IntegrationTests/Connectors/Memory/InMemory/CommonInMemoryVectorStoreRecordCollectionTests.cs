// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.InMemory;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.InMemory;

/// <summary>
/// Inherits common integration tests that should pass for any <see cref="VectorStoreCollection{TKey, TRecord}"/>.
/// </summary>
public class CommonInMemoryVectorStoreRecordCollectionTests() : BaseVectorStoreRecordCollectionTests<string>
{
    protected override string Key1 => "1";
    protected override string Key2 => "2";
    protected override string Key3 => "3";
    protected override string Key4 => "4";

    protected override VectorStoreCollection<string, TRecord> GetTargetRecordCollection<TRecord>(string recordCollectionName, VectorStoreCollectionDefinition? definition)
    {
        return new InMemoryCollection<string, TRecord>(recordCollectionName, new()
        {
            Definition = definition
        });
    }

    protected override HashSet<string> GetSupportedDistanceFunctions()
    {
        return [DistanceFunction.CosineDistance, DistanceFunction.CosineSimilarity, DistanceFunction.DotProductSimilarity, DistanceFunction.EuclideanDistance];
    }
}
