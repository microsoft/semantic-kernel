// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Weaviate.ConformanceTests.Support;
using Xunit;

namespace Weaviate.ConformanceTests.ModelTests;

public class WeaviateBasicModelTests_NamedVectors(WeaviateBasicModelTests_NamedVectors.Fixture fixture)
    : BasicModelTests<Guid>(fixture), IClassFixture<WeaviateBasicModelTests_NamedVectors.Fixture>
{
    public new class Fixture : BasicModelTests<Guid>.Fixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;
    }
}

public class WeaviateBasicModelTests_UnnamedVectors(WeaviateBasicModelTests_UnnamedVectors.Fixture fixture)
    : BasicModelTests<Guid>(fixture), IClassFixture<WeaviateBasicModelTests_UnnamedVectors.Fixture>
{
    public new class Fixture : BasicModelTests<Guid>.Fixture
    {
        public override TestStore TestStore => WeaviateTestStore.UnnamedVectorInstance;
    }
}
