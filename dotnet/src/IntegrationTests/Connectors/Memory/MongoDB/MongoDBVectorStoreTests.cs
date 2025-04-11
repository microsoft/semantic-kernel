// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.MongoDB;
using SemanticKernel.IntegrationTests.Connectors.Memory;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.MongoDB;

[Collection("MongoDBVectorStoreCollection")]
public class MongoDBVectorStoreTests(MongoDBVectorStoreFixture fixture)
    : BaseVectorStoreTests<string, MongoDBHotel>(new MongoDBVectorStore(fixture.MongoDatabase))
{
}
