// Copyright (c) Microsoft. All rights reserved.

using Qdrant.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Qdrant.ConformanceTests;

public class QdrantFilterTests(QdrantFilterTests.Fixture fixture)
    : FilterTests<ulong>(fixture), IClassFixture<QdrantFilterTests.Fixture>
{
    public new class Fixture : FilterTests<ulong>.Fixture
    {
        public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;
    }
}
