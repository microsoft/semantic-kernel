// Copyright (c) Microsoft. All rights reserved.

using AzureAISearch.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace AzureAISearch.ConformanceTests.ModelTests;

public class AzureAISearchNoDataModelTests(AzureAISearchNoDataModelTests.Fixture fixture)
    : NoDataModelTests<string>(fixture), IClassFixture<AzureAISearchNoDataModelTests.Fixture>
{
    public new class Fixture : NoDataModelTests<string>.Fixture
    {
        public override TestStore TestStore => AzureAISearchTestStore.Instance;
    }
}
