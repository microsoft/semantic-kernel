// Copyright (c) Microsoft. All rights reserved.

using Pinecone.ConformanceTests.Support;
using VectorData.ConformanceTests.Collections;
using Xunit;

namespace Pinecone.ConformanceTests.Collections;

public class PineconeCollectionConformanceTests(PineconeFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<PineconeFixture>
{
    // https://docs.pinecone.io/troubleshooting/restrictions-on-index-names
    public override string CollectionName => "collection-tests";
}
