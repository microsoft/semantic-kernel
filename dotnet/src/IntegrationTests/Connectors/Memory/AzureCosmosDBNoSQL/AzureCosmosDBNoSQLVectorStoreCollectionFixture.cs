// Copyright (c) Microsoft. All rights reserved.

using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureCosmosDBNoSQL;

[CollectionDefinition("AzureCosmosDBNoSQLVectorStoreCollection")]
public class AzureCosmosDBNoSQLVectorStoreCollectionFixture : ICollectionFixture<AzureCosmosDBNoSQLVectorStoreFixture>
{ }
