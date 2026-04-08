// Copyright (c) Microsoft. All rights reserved.

using InMemory.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace InMemory.ConformanceTests;

public class InMemoryDistanceFunctionTests(InMemoryDistanceFunctionTests.Fixture fixture)
    : DistanceFunctionTests<int>(fixture), IClassFixture<InMemoryDistanceFunctionTests.Fixture>
{
    public override Task EuclideanSquaredDistance() => Assert.ThrowsAsync<NotSupportedException>(base.EuclideanSquaredDistance);
    public override Task NegativeDotProductSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.NegativeDotProductSimilarity);
    public override Task HammingDistance() => Assert.ThrowsAsync<NotSupportedException>(base.HammingDistance);
    public override Task ManhattanDistance() => Assert.ThrowsAsync<NotSupportedException>(base.ManhattanDistance);

    public new class Fixture() : DistanceFunctionTests<int>.Fixture
    {
        public override TestStore TestStore => InMemoryTestStore.Instance;
    }
}
