// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureAISearch;

/// <summary>
/// Contains integration tests for the <see cref="AzureAISearchVectorStore"/> class.
/// Tests work with an Azure AI Search Instance.
/// </summary>
[Collection("AzureAISearchVectorStoreCollection")]
public class AzureAISearchVectorStoreTests(AzureAISearchVectorStoreFixture fixture)
    : BaseVectorStoreTests<string, AzureAISearchHotel>(new AzureAISearchVectorStore(fixture.SearchIndexClient))
{
    // If null, all tests will be enabled
    private const string SkipReason = "Requires Azure AI Search Service instance up and running";

    [Fact(Skip = SkipReason)]
    public override async Task ItCanGetAListOfExistingCollectionNamesAsync()
    {
        await base.ItCanGetAListOfExistingCollectionNamesAsync();
    }
}
