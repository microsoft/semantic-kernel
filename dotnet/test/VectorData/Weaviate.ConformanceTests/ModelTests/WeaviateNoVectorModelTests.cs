// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Weaviate.ConformanceTests.Support;
using Xunit;

namespace Weaviate.ConformanceTests.ModelTests;

public class WeaviateNoVectorModelTests(WeaviateNoVectorModelTests.Fixture fixture)
    : NoVectorModelTests<Guid>(fixture), IClassFixture<WeaviateNoVectorModelTests.Fixture>
{
    public new class Fixture : NoVectorModelTests<Guid>.Fixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;
    }
}
