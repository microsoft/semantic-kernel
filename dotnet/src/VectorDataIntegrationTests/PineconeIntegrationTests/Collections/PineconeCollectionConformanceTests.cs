// Copyright (c) Microsoft. All rights reserved.

using PineconeIntegrationTests.Support;
using VectorDataSpecificationTests.Collections;
using Xunit;

namespace PineconeIntegrationTests.Collections;

public class PineconeCollectionConformanceTests(PineconeFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<PineconeFixture>
{
    // https://docs.pinecone.io/troubleshooting/restrictions-on-index-names
    public override string CollectionName => "collection-tests";
}
