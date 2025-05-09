// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using SemanticKernel.IntegrationTests.Connectors.Memory.Xunit;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Weaviate;

/// <summary>
/// Inherits common integration tests that should pass for any <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.
/// </summary>
/// <param name="fixture">Weaviate setup and teardown.</param>
[Collection("WeaviateVectorStoreCollection")]
[DisableVectorStoreTests(Skip = "Weaviate tests are failing on the build server with connection reset errors, but passing locally.")]
public class CommonWeaviateVectorStoreRecordCollectionTests(WeaviateVectorStoreFixture fixture) : BaseVectorStoreRecordCollectionTests<Guid>
{
    protected override Guid Key1 => new("11111111-1111-1111-1111-111111111111");
    protected override Guid Key2 => new("22222222-2222-2222-2222-222222222222");
    protected override Guid Key3 => new("33333333-3333-3333-3333-333333333333");
    protected override Guid Key4 => new("44444444-4444-4444-4444-444444444444");

    protected override int DelayAfterUploadInMilliseconds => 1000;

    protected override IVectorStoreRecordCollection<Guid, TRecord> GetTargetRecordCollection<TRecord>(string recordCollectionName, VectorStoreRecordDefinition? vectorStoreRecordDefinition)
    {
        // Weaviate collection names must start with an upper case letter.
        var recordCollectionNameChars = recordCollectionName.ToCharArray();
        recordCollectionNameChars[0] = char.ToUpperInvariant(recordCollectionNameChars[0]);

        return new WeaviateVectorStoreRecordCollection<Guid, TRecord>(fixture.HttpClient!, new string(recordCollectionNameChars), new()
        {
            VectorStoreRecordDefinition = vectorStoreRecordDefinition
        });
    }

    protected override HashSet<string> GetSupportedDistanceFunctions()
    {
        return [DistanceFunction.CosineDistance, DistanceFunction.NegativeDotProductSimilarity, DistanceFunction.EuclideanSquaredDistance, DistanceFunction.Hamming, DistanceFunction.ManhattanDistance];
    }
}
