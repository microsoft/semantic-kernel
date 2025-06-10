// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace AzureAISearch.ConformanceTests.Support;

public class AzureAISearchSimpleModelFixture : SimpleModelFixture<string>
{
    public override string CollectionName => "simplemodel-" + AzureAISearchTestEnvironment.TestIndexPostfix;

    public override TestStore TestStore => AzureAISearchTestStore.Instance;
}
