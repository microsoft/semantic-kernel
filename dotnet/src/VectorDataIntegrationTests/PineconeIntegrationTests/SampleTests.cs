// Copyright (c) Microsoft. All rights reserved.

using Pinecone;
using PineconeIntegrationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace PineconeIntegrationTests;

public class SampleTests(PineconeFixture fixture) : IClassFixture<PineconeFixture>
{
    [ConditionalFact]
    public async Task CanRunSampleCode()
    {
        var collectionModel = await fixture.Client.CreateCollectionAsync(new CreateCollectionRequest
        {
            Name = "example-collection",
            Source = "example-index",
        });

        await fixture.Client.DeleteCollectionAsync(collectionModel.Name);
    }
}
