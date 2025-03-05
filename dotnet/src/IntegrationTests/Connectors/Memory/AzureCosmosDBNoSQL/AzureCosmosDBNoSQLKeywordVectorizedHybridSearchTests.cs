// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureCosmosDBNoSQL;

/// <summary>
/// Inherits common integration tests that should pass for any <see cref="IKeywordHybridSearch{TRecord}"/>.
/// </summary>
[Collection("AzureCosmosDBNoSQLVectorStoreCollection")]
[AzureCosmosDBNoSQLConnectionStringSetCondition]
public class AzureCosmosDBNoSQLKeywordVectorizedHybridSearchTests(AzureCosmosDBNoSQLVectorStoreFixture fixture) : BaseKeywordVectorizedHybridSearchTests<string>
{
    protected override string Key1 => "1";
    protected override string Key2 => "2";
    protected override string Key3 => "3";
    protected override string Key4 => "4";
    protected override int DelayAfterUploadInMilliseconds => 2000;
    protected override string? IndexKind { get; } = Microsoft.Extensions.VectorData.IndexKind.Flat;

    protected override IVectorStoreRecordCollection<string, TRecord> GetTargetRecordCollection<TRecord>(string recordCollectionName, VectorStoreRecordDefinition? vectorStoreRecordDefinition)
    {
        return new AzureCosmosDBNoSQLVectorStoreRecordCollection<TRecord>(fixture.Database!, recordCollectionName, new()
        {
            VectorStoreRecordDefinition = vectorStoreRecordDefinition
        });
    }
}
