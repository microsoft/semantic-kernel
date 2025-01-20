// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using SemanticKernel.IntegrationTests.Connectors.Memory.Xunit;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureAISearch;

/// <summary>
/// Contains integration tests for the <see cref="AzureAISearchVectorStore"/> class.
/// Tests work with an Azure AI Search Instance.
/// </summary>
[Collection("AzureAISearchVectorStoreCollection")]
[DisableVectorStoreTests(Skip = "Requires Azure AI Search Service instance up and running")]
public class AzureAISearchVectorStoreTests(AzureAISearchVectorStoreFixture fixture)
    : BaseVectorStoreTests<string, AzureAISearchHotel>(new AzureAISearchVectorStore(fixture.SearchIndexClient))
{
}
