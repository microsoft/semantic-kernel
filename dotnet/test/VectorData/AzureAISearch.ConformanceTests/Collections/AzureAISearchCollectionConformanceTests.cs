// Copyright (c) Microsoft. All rights reserved.

using AzureAISearch.ConformanceTests.Support;
using VectorData.ConformanceTests.Collections;
using Xunit;

namespace AzureAISearch.ConformanceTests.Collections;

public class AzureAISearchCollectionConformanceTests(AzureAISearchFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<AzureAISearchFixture>
{
    // Azure AI search only supports lowercase letters, digits or dashes.
    public override string CollectionName => "collection-tests";
}
