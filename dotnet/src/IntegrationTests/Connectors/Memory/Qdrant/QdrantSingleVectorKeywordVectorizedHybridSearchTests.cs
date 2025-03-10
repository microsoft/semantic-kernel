// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Qdrant;

/// <summary>
/// Inherits common integration tests that should pass for any <see cref="IKeywordHybridSearch{TRecord}"/>.
/// </summary>
[Collection("QdrantVectorStoreCollection")]
public class QdrantSingleVectorKeywordVectorizedHybridSearchTests(QdrantVectorStoreFixture fixture) : BaseKeywordVectorizedHybridSearchTests<ulong>
{
    protected override ulong Key1 => 1;
    protected override ulong Key2 => 2;
    protected override ulong Key3 => 3;
    protected override ulong Key4 => 4;

    protected override IVectorStoreRecordCollection<ulong, TRecord> GetTargetRecordCollection<TRecord>(string recordCollectionName, VectorStoreRecordDefinition? vectorStoreRecordDefinition)
    {
        return new QdrantVectorStoreRecordCollection<TRecord>(fixture.QdrantClient, recordCollectionName, new()
        {
            HasNamedVectors = false,
            VectorStoreRecordDefinition = vectorStoreRecordDefinition
        });
    }
}
