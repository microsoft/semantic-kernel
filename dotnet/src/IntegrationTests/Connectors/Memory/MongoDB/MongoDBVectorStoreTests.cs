// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.MongoDB;
using SemanticKernel.IntegrationTests.Connectors.Memory;
using SemanticKernel.IntegrationTests.Connectors.Memory.Xunit;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.MongoDB;

[Collection("MongoDBVectorStoreCollection")]
[DisableVectorStoreTests(Skip = "The MongoDB container is intermittently timing out at startup time blocking prs, so these test should be run manually.")]
public class MongoDBVectorStoreTests(MongoDBVectorStoreFixture fixture)
#pragma warning disable CA2000 // Dispose objects before losing scope
    : BaseVectorStoreTests<string, MongoDBHotel>(new MongoVectorStore(fixture.MongoDatabase))
#pragma warning restore CA2000 // Dispose objects before losing scope
{
}
