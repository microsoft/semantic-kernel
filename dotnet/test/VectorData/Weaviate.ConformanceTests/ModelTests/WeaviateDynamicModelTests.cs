// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Weaviate.ConformanceTests.Support;
using Xunit;

namespace Weaviate.ConformanceTests.ModelTests;

public class WeaviateDynamicModelTests_NamedVectors(WeaviateDynamicModelTests_NamedVectors.Fixture fixture)
    : DynamicModelTests<Guid>(fixture), IClassFixture<WeaviateDynamicModelTests_NamedVectors.Fixture>
{
    public new class Fixture : DynamicModelTests<Guid>.Fixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;
    }
}

public class WeaviateDynamicModelTests_UnnamedVectors(WeaviateDynamicModelTests_UnnamedVectors.Fixture fixture)
    : DynamicModelTests<Guid>(fixture), IClassFixture<WeaviateDynamicModelTests_UnnamedVectors.Fixture>
{
    public new class Fixture : DynamicModelTests<Guid>.Fixture
    {
        public override TestStore TestStore => WeaviateTestStore.UnnamedVectorInstance;
    }
}
