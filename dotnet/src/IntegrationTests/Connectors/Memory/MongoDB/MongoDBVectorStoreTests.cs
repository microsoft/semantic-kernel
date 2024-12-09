// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using SemanticKernel.IntegrationTests.Connectors.Memory;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.MongoDB;

[Collection("MongoDBVectorStoreCollection")]
public class MongoDBVectorStoreTests(MongoDBVectorStoreFixture fixture)
    : BaseVectorStoreTests<string, MongoDBHotel>(new MongoDBVectorStore(fixture.MongoDatabase))
{
    // If null, all tests will be enabled
    private const string? SkipReason = "The tests are for manual verification.";

    [Fact(Skip = SkipReason)]
    public override async Task ItCanGetAListOfExistingCollectionNamesAsync()
    {
        await base.ItCanGetAListOfExistingCollectionNamesAsync();
    }
}
