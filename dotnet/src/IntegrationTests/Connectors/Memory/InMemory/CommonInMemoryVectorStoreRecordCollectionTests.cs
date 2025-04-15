﻿// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.InMemory;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.InMemory;

/// <summary>
/// Inherits common integration tests that should pass for any <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.
/// </summary>
public class CommonInMemoryVectorStoreRecordCollectionTests() : BaseVectorStoreRecordCollectionTests<string>
{
    protected override string Key1 => "1";
    protected override string Key2 => "2";
    protected override string Key3 => "3";
    protected override string Key4 => "4";

    protected override IVectorStoreRecordCollection<string, TRecord> GetTargetRecordCollection<TRecord>(string recordCollectionName, VectorStoreRecordDefinition? vectorStoreRecordDefinition)
    {
        return new InMemoryVectorStoreRecordCollection<string, TRecord>(recordCollectionName, new()
        {
            VectorStoreRecordDefinition = vectorStoreRecordDefinition
        });
    }

    protected override HashSet<string> GetSupportedDistanceFunctions()
    {
        return [DistanceFunction.CosineDistance, DistanceFunction.CosineSimilarity, DistanceFunction.DotProductSimilarity, DistanceFunction.EuclideanDistance];
    }
}
