// Copyright (c) Microsoft. All rights reserved.

using AzureAISearch.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace AzureAISearch.ConformanceTests.ModelTests;

public class AzureAISearchMultiVectorModelTests(AzureAISearchMultiVectorModelTests.Fixture fixture)
    : MultiVectorModelTests<string>(fixture), IClassFixture<AzureAISearchMultiVectorModelTests.Fixture>
{
    public new class Fixture : MultiVectorModelTests<string>.Fixture
    {
        public override string CollectionName => "multi-vector-" + AzureAISearchTestEnvironment.TestIndexPostfix;

        public override TestStore TestStore => AzureAISearchTestStore.Instance;
    }
}
