// Copyright (c) Microsoft. All rights reserved.

using Qdrant.ConformanceTests.Support;
using VectorData.ConformanceTests.Filter;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Qdrant.ConformanceTests.Filter;

public class QdrantBasicFilterTests(QdrantBasicFilterTests.Fixture fixture)
    : BasicFilterTests<ulong>(fixture), IClassFixture<QdrantBasicFilterTests.Fixture>
{
    public new class Fixture : BasicFilterTests<ulong>.Fixture
    {
        public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;
    }
}
