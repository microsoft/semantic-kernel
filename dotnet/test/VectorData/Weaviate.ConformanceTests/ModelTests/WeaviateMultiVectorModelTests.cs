// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Weaviate.ConformanceTests.Support;
using Xunit;

namespace Weaviate.ConformanceTests.ModelTests;

public class WeaviateMultiVectorModelTests(WeaviateMultiVectorModelTests.Fixture fixture)
    : MultiVectorModelTests<Guid>(fixture), IClassFixture<WeaviateMultiVectorModelTests.Fixture>
{
    public new class Fixture : MultiVectorModelTests<Guid>.Fixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;
    }
}
