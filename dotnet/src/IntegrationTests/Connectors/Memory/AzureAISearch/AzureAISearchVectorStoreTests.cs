// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureAISearch;

/// <summary>
/// Contains integration tests for the <see cref="AzureAISearchVectorStore"/> class.
/// Tests work with an Azure AI Search Instance.
/// </summary>
[Collection("AzureAISearchVectorStoreCollection")]
public class AzureAISearchVectorStoreTests(ITestOutputHelper output, AzureAISearchVectorStoreFixture fixture)
{
    // If null, all tests will be enabled
    private const string SkipReason = "Requires Azure AI Search Service instance up and running";

    [Fact(Skip = SkipReason)]
    public async Task ItCanGetAListOfExistingCollectionNamesAsync()
    {
        // Arrange
        var additionalCollectionName = fixture.TestIndexName + "-listnames";
        await AzureAISearchVectorStoreFixture.DeleteIndexIfExistsAsync(additionalCollectionName, fixture.SearchIndexClient);
        await AzureAISearchVectorStoreFixture.CreateIndexAsync(additionalCollectionName, fixture.SearchIndexClient);
        var sut = new AzureAISearchVectorStore(fixture.SearchIndexClient);

        // Act
        var collectionNames = await sut.ListCollectionNamesAsync().ToListAsync();

        // Assert
        Assert.Equal(2, collectionNames.Where(x => x.StartsWith(fixture.TestIndexName, StringComparison.InvariantCultureIgnoreCase)).Count());
        Assert.Contains(fixture.TestIndexName, collectionNames);
        Assert.Contains(additionalCollectionName, collectionNames);

        // Output
        output.WriteLine(string.Join(",", collectionNames));

        // Cleanup
        await AzureAISearchVectorStoreFixture.DeleteIndexIfExistsAsync(additionalCollectionName, fixture.SearchIndexClient);
    }
}
