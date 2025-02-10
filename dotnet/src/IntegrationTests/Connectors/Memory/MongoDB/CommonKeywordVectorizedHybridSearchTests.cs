// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using SemanticKernel.IntegrationTests.Connectors.MongoDB;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.MongoDB;

/// <summary>
/// Inherits common integration tests that should pass for any <see cref="IKeywordVectorizedHybridSearch{TRecord}"/>.
/// </summary>
/// <param name="fixture">Azure AI Search setup and teardown.</param>
[Collection("MongoDBVectorStoreCollection")]
public class CommonKeywordVectorizedHybridSearchTests(MongoDBVectorStoreFixture fixture) : BaseKeywordVectorizedHybridSearchTests<string>
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
