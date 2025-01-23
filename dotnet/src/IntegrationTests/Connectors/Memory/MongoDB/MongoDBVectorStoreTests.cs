// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.MongoDB;
using SemanticKernel.IntegrationTests.Connectors.Memory;
using SemanticKernel.IntegrationTests.Connectors.Memory.Xunit;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.MongoDB;

[Collection("MongoDBVectorStoreCollection")]
[DisableVectorStoreTests(Skip = "The tests are for manual verification.")]
public class MongoDBVectorStoreTests(MongoDBVectorStoreFixture fixture)
    : BaseVectorStoreTests<string, MongoDBHotel>(new MongoDBVectorStore(fixture.MongoDatabase))
{
}
