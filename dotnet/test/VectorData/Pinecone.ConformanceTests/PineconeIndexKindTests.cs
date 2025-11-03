// Copyright (c) Microsoft. All rights reserved.

using Pinecone.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace Pinecone.ConformanceTests;

public class PineconeIndexKindTests(PineconeIndexKindTests.Fixture fixture)
    : IndexKindTests<string>(fixture), IClassFixture<PineconeIndexKindTests.Fixture>
{
    // Pinecone does not support index-less searching
    public override Task Flat() => Assert.ThrowsAsync<NotSupportedException>(base.Flat);

    [ConditionalFact]
    public virtual Task PGA()
        => this.Test("PGA");

    protected override async Task Test(string indexKind)
    {
        await base.Test(indexKind);

        // The Pinecone emulator needs some extra time to spawn a new index service
        // that uses a different distance function.
        await Task.Delay(TimeSpan.FromSeconds(5));
    }

    public new class Fixture() : IndexKindTests<string>.Fixture
    {
        public override TestStore TestStore => PineconeTestStore.Instance;

        // https://docs.pinecone.io/troubleshooting/restrictions-on-index-names
        public override string CollectionName => "index-kind-tests";
    }
}
