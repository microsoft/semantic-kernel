// Copyright (c) Microsoft. All rights reserved.

using AzureAISearchIntegrationTests.Support;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

#pragma warning disable CA2000 // Dispose objects before losing scope

namespace AzureAISearchIntegrationTests;

public class AzureAISearchEmbeddingTypeTests(AzureAISearchEmbeddingTypeTests.Fixture fixture)
    : EmbeddingTypeTests<string>(fixture), IClassFixture<AzureAISearchEmbeddingTypeTests.Fixture>
{
    public new class Fixture : EmbeddingTypeTests<string>.Fixture
    {
        public override TestStore TestStore => AzureAISearchTestStore.Instance;

        // Azure AI search only supports lowercase letters, digits or dashes.
        public override string CollectionName => "embedding-type-tests" + AzureAISearchTestEnvironment.TestIndexPostfix;
    }
}
