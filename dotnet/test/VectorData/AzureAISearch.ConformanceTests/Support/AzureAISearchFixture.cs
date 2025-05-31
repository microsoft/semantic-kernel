// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace AzureAISearchIntegrationTests.Support;

public class AzureAISearchFixture : VectorStoreFixture
{
    public override TestStore TestStore => AzureAISearchTestStore.Instance;
}
