// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using SemanticKernel.IntegrationTests.Connectors.Memory.Pinecone.Xunit;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Pinecone;

/// <summary>
/// Inherits common integration tests that should pass for any <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.
/// </summary>
/// <param name="fixture">Pinecone setup and teardown.</param>
[Collection("PineconeVectorStoreTests")]
[PineconeApiKeySetCondition]
public class CommonPineconeVectorStoreRecordCollectionTests(PineconeVectorStoreFixture fixture) : BaseVectorStoreRecordCollectionTests<string>, IClassFixture<PineconeVectorStoreFixture>
{
    protected override string Key1 => "1";
    protected override string Key2 => "2";
    protected override string Key3 => "3";
    protected override string Key4 => "4";

    protected override int DelayAfterIndexCreateInMilliseconds => 2000;

    protected override int DelayAfterUploadInMilliseconds => 15000;

    [SuppressMessage("Globalization", "CA1308:Normalize strings to uppercase", Justification = "Pinecone collection names should be lower case.")]
    protected override IVectorStoreRecordCollection<string, TRecord> GetTargetRecordCollection<TRecord>(string recordCollectionName, VectorStoreRecordDefinition? vectorStoreRecordDefinition)
    {
        return new PineconeVectorStoreRecordCollection<TRecord>(fixture.Client, recordCollectionName.ToLowerInvariant(), new()
        {
            VectorStoreRecordDefinition = vectorStoreRecordDefinition
        });
    }

    protected override HashSet<string> GetSupportedDistanceFunctions()
    {
        return [DistanceFunction.CosineSimilarity, DistanceFunction.DotProductSimilarity, DistanceFunction.EuclideanSquaredDistance];
    }
}
