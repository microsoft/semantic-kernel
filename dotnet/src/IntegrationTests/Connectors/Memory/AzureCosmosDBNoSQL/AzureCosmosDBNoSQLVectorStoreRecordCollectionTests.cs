// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureCosmosDBNoSQL;

[Collection("AzureCosmosDBNoSQLVectorStoreCollection")]
public sealed class AzureCosmosDBNoSQLVectorStoreRecordCollectionTests(AzureCosmosDBNoSQLVectorStoreFixture fixture)
{
    //private const string? SkipReason = "Azure CosmosDB NoSQL cluster is required";
    private const string? SkipReason = null;

    [Theory(Skip = SkipReason)]
    [InlineData("sk-test-hotels", true)]
    [InlineData("nonexistentcollection", false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(string collectionName, bool expectedExists)
    {
        // Arrange
        var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<AzureCosmosDBNoSQLHotel>(fixture.Database!, collectionName);

        // Act
        var actual = await sut.CollectionExistsAsync();

        // Assert
        Assert.Equal(expectedExists, actual);
    }
}
