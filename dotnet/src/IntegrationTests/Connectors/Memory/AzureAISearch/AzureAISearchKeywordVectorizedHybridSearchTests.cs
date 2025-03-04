// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureAISearch;

/// <summary>
/// Inherits common integration tests that should pass for any <see cref="IKeywordHybridSearch{TRecord}"/>.
/// </summary>
/// <param name="fixture">Azure AI Search setup and teardown.</param>
[Collection("AzureAISearchVectorStoreCollection")]
[AzureAISearchConfigCondition]
public class AzureAISearchKeywordVectorizedHybridSearchTests(AzureAISearchVectorStoreFixture fixture) : BaseKeywordVectorizedHybridSearchTests<string>
{
    protected override string Key1 => "1";
    protected override string Key2 => "2";
    protected override string Key3 => "3";
    protected override string Key4 => "4";
    protected override int DelayAfterUploadInMilliseconds => 2000;

    protected override IVectorStoreRecordCollection<string, TRecord> GetTargetRecordCollection<TRecord>(string recordCollectionName, VectorStoreRecordDefinition? vectorStoreRecordDefinition)
    {
        return new AzureAISearchVectorStoreRecordCollection<TRecord>(fixture.SearchIndexClient, recordCollectionName + AzureAISearchVectorStoreFixture.TestIndexPostfix, new()
        {
            VectorStoreRecordDefinition = vectorStoreRecordDefinition
        });
    }
}
