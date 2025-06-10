// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace AzureAISearch.ConformanceTests.Support;

public class AzureAISearchFixture : VectorStoreFixture
{
    public override TestStore TestStore => AzureAISearchTestStore.Instance;
}
