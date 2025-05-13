// Copyright (c) Microsoft. All rights reserved.

using AzureAISearchIntegrationTests.Support;
using VectorDataSpecificationTests.Collections;
using Xunit;

namespace AzureAISearchIntegrationTests.Collections;

public class AzureAISearchCollectionConformanceTests(AzureAISearchFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<AzureAISearchFixture>
{
    // Azure AI search only supports lowercase letters, digits or dashes.
    public override string CollectionName => "collection-tests";
}
