// Copyright (c) Microsoft. All rights reserved.

using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureAISearch;

[CollectionDefinition("AzureAISearchMemoryCollection")]
public class AzureAISearchMemoryCollectionFixture : ICollectionFixture<AzureAISearchMemoryFixture>
{
}
