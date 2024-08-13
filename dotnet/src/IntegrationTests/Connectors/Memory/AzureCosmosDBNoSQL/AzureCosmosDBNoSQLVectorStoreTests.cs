// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureCosmosDBNoSQL;

/// <summary>
/// Integration tests for <see cref="AzureCosmosDBNoSQLVectorStore"/>.
/// </summary>
[Collection("AzureCosmosDBNoSQLVectorStoreCollection")]
public sealed class AzureCosmosDBNoSQLVectorStoreTests(AzureCosmosDBNoSQLVectorStoreFixture fixture)
{
    private const string? SkipReason = "Azure CosmosDB NoSQL cluster is required";

    [Fact(Skip = SkipReason)]
    public async Task ItCanGetAListOfExistingCollectionNamesAsync()
    {
        // Arrange
        var sut = new AzureCosmosDBNoSQLVectorStore(fixture.Database!);

        await fixture.Database!.CreateContainerIfNotExistsAsync(new ContainerProperties("sk-test-hotels", "/id"));
        await fixture.Database!.CreateContainerIfNotExistsAsync(new ContainerProperties("sk-test-contacts", "/id"));

        // Act
        var collectionNames = await sut.ListCollectionNamesAsync().ToListAsync();

        // Assert
        Assert.Contains("sk-test-hotels", collectionNames);
        Assert.Contains("sk-test-contacts", collectionNames);
    }
}
