// Copyright (c) Microsoft. All rights reserved.

using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.CosmosMongoDB;

[CollectionDefinition("CosmosMongoCollection")]
public class CosmosMongoCollectionFixture : ICollectionFixture<CosmosMongoVectorStoreFixture>
{ }
