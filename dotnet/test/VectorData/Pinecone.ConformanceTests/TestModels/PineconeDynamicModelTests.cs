// Copyright (c) Microsoft. All rights reserved.

using Pinecone.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Pinecone.ConformanceTests.ModelTests;

public class PineconeDynamicModelTests(PineconeDynamicModelTests.Fixture fixture)
    : DynamicModelTests<string>(fixture), IClassFixture<PineconeDynamicModelTests.Fixture>
{
    public new class Fixture : DynamicModelTests<string>.Fixture
    {
        public override TestStore TestStore => PineconeTestStore.Instance;
    }
}
