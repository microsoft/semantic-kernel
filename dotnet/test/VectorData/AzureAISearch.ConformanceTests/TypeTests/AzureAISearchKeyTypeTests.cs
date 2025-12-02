// Copyright (c) Microsoft. All rights reserved.

using AzureAISearch.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace AzureAISearch.ConformanceTests.TypeTests;

public class AzureAISearchKeyTypeTests(AzureAISearchKeyTypeTests.Fixture fixture)
    : KeyTypeTests(fixture), IClassFixture<AzureAISearchKeyTypeTests.Fixture>
{
    [ConditionalFact]
    public virtual Task String() => this.Test<string>("foo", "bar");

    public new class Fixture : KeyTypeTests.Fixture
    {
        public override TestStore TestStore => AzureAISearchTestStore.Instance;
    }
}
