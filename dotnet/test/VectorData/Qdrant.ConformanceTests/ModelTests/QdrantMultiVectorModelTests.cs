// Copyright (c) Microsoft. All rights reserved.

using Qdrant.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Qdrant.ConformanceTests.ModelTests;

public class QdrantMultiVectorModelTests(QdrantMultiVectorModelTests.Fixture fixture)
    : MultiVectorModelTests<ulong>(fixture), IClassFixture<QdrantMultiVectorModelTests.Fixture>
{
    public new class Fixture : MultiVectorModelTests<ulong>.Fixture
    {
        public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;
    }
}
