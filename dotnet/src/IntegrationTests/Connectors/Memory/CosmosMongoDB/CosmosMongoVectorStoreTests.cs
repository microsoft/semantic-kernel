// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.CosmosMongoDB;
using SemanticKernel.IntegrationTests.Connectors.Memory;
using SemanticKernel.IntegrationTests.Connectors.Memory.Xunit;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.CosmosMongoDB;

[Collection("CosmosMongoCollection")]
[DisableVectorStoreTests(Skip = "Azure CosmosDB MongoDB cluster is required")]
public class CosmosMongoVectorStoreTests(CosmosMongoVectorStoreFixture fixture)
#pragma warning disable CA2000 // Dispose objects before losing scope
    : BaseVectorStoreTests<string, CosmosMongoHotel>(new CosmosMongoVectorStore(fixture.MongoDatabase))
#pragma warning restore CA2000 // Dispose objects before losing scope
{
}
