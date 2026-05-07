// Copyright (c) Microsoft. All rights reserved.

using AzureAISearch.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace AzureAISearch.ConformanceTests;

public class AzureAISearchHybridSearchTests(
    AzureAISearchHybridSearchTests.VectorAndStringFixture vectorAndStringFixture,
    AzureAISearchHybridSearchTests.MultiTextFixture multiTextFixture)
    : HybridSearchTests<string>(vectorAndStringFixture, multiTextFixture),
        IClassFixture<AzureAISearchHybridSearchTests.VectorAndStringFixture>,
        IClassFixture<AzureAISearchHybridSearchTests.MultiTextFixture>
{
    public new class VectorAndStringFixture : HybridSearchTests<string>.VectorAndStringFixture
    {
        public override TestStore TestStore => AzureAISearchTestStore.Instance;
    }

    public new class MultiTextFixture : HybridSearchTests<string>.MultiTextFixture
    {
        public override TestStore TestStore => AzureAISearchTestStore.Instance;
    }
}
