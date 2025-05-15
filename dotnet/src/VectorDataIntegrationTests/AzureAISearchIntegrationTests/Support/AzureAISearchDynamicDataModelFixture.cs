// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace AzureAISearchIntegrationTests.Support;

public class AzureAISearchDynamicDataModelFixture : DynamicDataModelFixture<string>
{
    public override string CollectionName => "dynamicdatamodel-" + AzureAISearchTestEnvironment.TestIndexPostfix;

    public override TestStore TestStore => AzureAISearchTestStore.Instance;
}
