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
#pragma warning disable CA2000 // Dispose objects before losing scope
    : BaseVectorStoreTests<string, AzureAISearchHotel>(new AzureAISearchVectorStore(fixture.SearchIndexClient))
#pragma warning restore CA2000 // Dispose objects before losing scope
{
}
