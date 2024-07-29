// Copyright (c) Microsoft. All rights reserved.

using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureCosmosDBMongoDB;

[CollectionDefinition("AzureCosmosDBMongoDBVectorStoreCollection")]
public class AzureCosmosDBMongoDBVectorStoreCollectionFixture : ICollectionFixture<AzureCosmosDBMongoDBVectorStoreFixture>
{ }
