// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Redis;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Redis;

// Disable unused class warning, as this class is marked internal to disable the tests in the base class.
#pragma warning disable CA1812
#pragma warning disable CA1852

/// <summary>
/// Inherits common integration tests that should pass for any <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.
/// </summary>
/// <param name="fixture">Redis setup and teardown.</param>
[Collection("RedisVectorStoreCollection")]
internal class CommonRedisHashsetVectorStoreRecordCollectionTests(RedisVectorStoreFixture fixture) : BaseVectorStoreRecordCollectionTests<string>
{
    protected override string Key1 => "1";
    protected override string Key2 => "2";
    protected override string Key3 => "3";
    protected override string Key4 => "4";

    protected override IVectorStoreRecordCollection<string, TRecord> GetTargetRecordCollection<TRecord>(string recordCollectionName, VectorStoreRecordDefinition? vectorStoreRecordDefinition)
    {
        return new RedisHashSetVectorStoreRecordCollection<TRecord>(fixture.Database, recordCollectionName + "hashset", new()
        {
            VectorStoreRecordDefinition = vectorStoreRecordDefinition
        });
    }

    protected override HashSet<string> GetSupportedDistanceFunctions()
    {
        // Excluding DotProductSimilarity from the test even though Redis supports it, because the values that redis returns
        // are neither DotProductSimilarity nor NegativeDotProduct, but rather 1 - DotProductSimilarity.
        return [DistanceFunction.CosineDistance, DistanceFunction.CosineSimilarity, DistanceFunction.EuclideanSquaredDistance];
    }
}
