// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.MongoDB;
using SemanticKernel.IntegrationTests.Connectors.Memory;
using SemanticKernel.IntegrationTests.Connectors.Memory.Xunit;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.MongoDB;

[Collection("MongoDBVectorStoreCollection")]
[DisableVectorStoreTests(Skip = "The MongoDB container is intermittently timing out at startup time blocking prs, so these test should be run manually.")]
public class MongoDBVectorStoreTests(MongoDBVectorStoreFixture fixture)
    : BaseVectorStoreTests<string, MongoDBHotel>(new MongoDBVectorStore(fixture.MongoDatabase))
{
}
