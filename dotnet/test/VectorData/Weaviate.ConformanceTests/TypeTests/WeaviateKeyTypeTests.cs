// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using Weaviate.ConformanceTests.Support;
using Xunit;

namespace Weaviate.ConformanceTests.TypeTests;

public class WeaviateKeyTypeTests(WeaviateKeyTypeTests.Fixture fixture)
    : KeyTypeTests(fixture), IClassFixture<WeaviateKeyTypeTests.Fixture>
{
    public new class Fixture : KeyTypeTests.Fixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;
    }
}
