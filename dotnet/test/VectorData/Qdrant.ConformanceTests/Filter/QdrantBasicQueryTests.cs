// Copyright (c) Microsoft. All rights reserved.

using Qdrant.ConformanceTests.Support;
using VectorData.ConformanceTests.Filter;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Qdrant.ConformanceTests.Filter;

public class QdrantBasicQueryTests(QdrantBasicQueryTests.Fixture fixture)
    : BasicQueryTests<ulong>(fixture), IClassFixture<QdrantBasicQueryTests.Fixture>
{
    public new class Fixture : BasicQueryTests<ulong>.QueryFixture
    {
        public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;
    }
}
