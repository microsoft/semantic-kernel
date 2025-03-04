// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using SemanticKernel.IntegrationTests.Connectors.Memory;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.MongoDB;

/// <summary>
/// Inherits common integration tests that should pass for any <see cref="IKeywordHybridSearch{TRecord}"/>.
/// </summary>
[Collection("MongoDBVectorStoreCollection")]
public class MongoDBKeywordVectorizedHybridSearchTests(MongoDBVectorStoreFixture fixture) : BaseKeywordVectorizedHybridSearchTests<string>
{
    protected override string Key1 => "1";
    protected override string Key2 => "2";
    protected override string Key3 => "3";
    protected override string Key4 => "4";
    protected override int DelayAfterUploadInMilliseconds => 1000;

    protected override IVectorStoreRecordCollection<string, TRecord> GetTargetRecordCollection<TRecord>(string recordCollectionName, VectorStoreRecordDefinition? vectorStoreRecordDefinition)
    {
        return new MongoDBVectorStoreRecordCollection<TRecord>(fixture.MongoDatabase, recordCollectionName, new()
        {
            VectorStoreRecordDefinition = vectorStoreRecordDefinition
        });
    }
}
