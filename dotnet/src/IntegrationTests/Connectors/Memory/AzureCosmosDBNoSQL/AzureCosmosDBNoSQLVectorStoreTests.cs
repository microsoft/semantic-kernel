// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using SemanticKernel.IntegrationTests.Connectors.Memory.Xunit;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureCosmosDBNoSQL;

/// <summary>
/// Integration tests for <see cref="AzureCosmosDBNoSQLVectorStore"/>.
/// </summary>
[Collection("AzureCosmosDBNoSQLVectorStoreCollection")]
[DisableVectorStoreTests(Skip = "Azure CosmosDB NoSQL cluster is required")]
public sealed class AzureCosmosDBNoSQLVectorStoreTests(AzureCosmosDBNoSQLVectorStoreFixture fixture)
    : BaseVectorStoreTests<string, AzureCosmosDBNoSQLHotel>(new AzureCosmosDBNoSQLVectorStore(fixture.Database!))
{
}
