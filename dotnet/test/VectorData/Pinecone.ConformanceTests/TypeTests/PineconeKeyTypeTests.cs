// Copyright (c) Microsoft. All rights reserved.

using Pinecone.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace Pinecone.ConformanceTests.TypeTests;

public class PineconeKeyTypeTests(PineconeKeyTypeTests.Fixture fixture)
    : KeyTypeTests(fixture), IClassFixture<PineconeKeyTypeTests.Fixture>
{
    [ConditionalFact]
    public virtual Task String() => this.Test<string>("foo");

    public new class Fixture : KeyTypeTests.Fixture
    {
        public override TestStore TestStore => PineconeTestStore.Instance;
    }
}
