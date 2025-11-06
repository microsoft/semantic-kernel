// Copyright (c) Microsoft. All rights reserved.

using Pinecone.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Pinecone.ConformanceTests.ModelTests;

public class PineconeBasicModelTests(PineconeBasicModelTests.Fixture fixture)
    : BasicModelTests<string>(fixture), IClassFixture<PineconeBasicModelTests.Fixture>
{
    public override async Task GetAsync_with_filter_and_OrderBy()
    {
        var exception = await Assert.ThrowsAsync<NotSupportedException>(base.GetAsync_with_filter_and_OrderBy);
        Assert.Equal("Pinecone does not support ordering.", exception.Message);
    }

    public override async Task GetAsync_with_filter_and_multiple_OrderBys()
    {
        var exception = await Assert.ThrowsAsync<NotSupportedException>(base.GetAsync_with_filter_and_multiple_OrderBys);
        Assert.Equal("Pinecone does not support ordering.", exception.Message);
    }

    public override async Task GetAsync_with_filter_and_OrderBy_and_Skip()
    {
        var exception = await Assert.ThrowsAsync<NotSupportedException>(base.GetAsync_with_filter_and_OrderBy_and_Skip);
        Assert.Equal("Pinecone does not support ordering.", exception.Message);
    }

    public new class Fixture : BasicModelTests<string>.Fixture
    {
        public override TestStore TestStore => PineconeTestStore.Instance;
    }
}
