// Copyright (c) Microsoft. All rights reserved.

using Pinecone.ConformanceTests.Support;
using VectorData.ConformanceTests;
using Xunit;

namespace Pinecone.ConformanceTests;

public class PineconeCollectionManagementTests(PineconeFixture fixture)
    : CollectionManagementTests<string>(fixture), IClassFixture<PineconeFixture>
{
    // https://docs.pinecone.io/troubleshooting/restrictions-on-index-names
    public override string CollectionName => "collection-tests";
}
