// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace AzureAISearch.ConformanceTests.Support;

public class AzureAISearchDynamicDataModelFixture : DynamicDataModelFixture<string>
{
    public override string CollectionName => "dynamicdatamodel-" + AzureAISearchTestEnvironment.TestIndexPostfix;

    public override TestStore TestStore => AzureAISearchTestStore.Instance;
}
