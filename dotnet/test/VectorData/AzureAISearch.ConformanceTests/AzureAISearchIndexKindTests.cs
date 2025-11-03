// Copyright (c) Microsoft. All rights reserved.

using AzureAISearch.ConformanceTests.Support;
using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace AzureAISearch.ConformanceTests;

public class AzureAISearchIndexKindTests(AzureAISearchIndexKindTests.Fixture fixture)
    : IndexKindTests<string>(fixture), IClassFixture<AzureAISearchIndexKindTests.Fixture>
{
    [ConditionalFact]
    public virtual Task Hnsw()
        => this.Test(IndexKind.Hnsw);

    public new class Fixture() : IndexKindTests<string>.Fixture
    {
        public override string CollectionName => "index-kind-" + AzureAISearchTestEnvironment.TestIndexPostfix;

        public override TestStore TestStore => AzureAISearchTestStore.Instance;
    }
}
