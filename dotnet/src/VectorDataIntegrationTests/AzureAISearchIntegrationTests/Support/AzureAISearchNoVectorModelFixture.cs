// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace AzureAISearchIntegrationTests.Support;

public class AzureAISearchNoVectorModelFixture : NoVectorModelFixture<string>
{
    public override TestStore TestStore => AzureAISearchTestStore.Instance;
}
