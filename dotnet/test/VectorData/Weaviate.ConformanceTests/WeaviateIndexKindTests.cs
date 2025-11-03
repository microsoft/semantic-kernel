// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Weaviate.ConformanceTests.Support;
using Xunit;

namespace Weaviate.ConformanceTests;

public class WeaviateIndexKindTests(WeaviateIndexKindTests.Fixture fixture)
    : IndexKindTests<Guid>(fixture), IClassFixture<WeaviateIndexKindTests.Fixture>
{
    [ConditionalFact]
    public virtual Task Hnsw()
        => this.Test(IndexKind.Hnsw);

    [ConditionalFact]
    public virtual Task Dynamic()
        => this.Test(IndexKind.Dynamic);

    public new class Fixture() : IndexKindTests<Guid>.Fixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;
    }
}
