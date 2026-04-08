// Copyright (c) Microsoft. All rights reserved.

using AzureAISearch.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace AzureAISearch.ConformanceTests.ModelTests;

public class AzureAISearchBasicModelTests(AzureAISearchBasicModelTests.Fixture fixture)
    : BasicModelTests<string>(fixture), IClassFixture<AzureAISearchBasicModelTests.Fixture>
{
    public new class Fixture : BasicModelTests<string>.Fixture
    {
        public override TestStore TestStore => AzureAISearchTestStore.Instance;
    }
}
