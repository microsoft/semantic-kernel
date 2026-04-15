// Copyright (c) Microsoft. All rights reserved.

using Qdrant.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using Xunit;

namespace Qdrant.ConformanceTests.TypeTests;

public class QdrantKeyTypeTests(QdrantKeyTypeTests.Fixture fixture)
    : KeyTypeTests(fixture), IClassFixture<QdrantKeyTypeTests.Fixture>
{
    [Fact]
    public virtual Task ULong() => this.Test<ulong>(8UL);

    public new class Fixture : KeyTypeTests.Fixture
    {
        public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;
    }
}
