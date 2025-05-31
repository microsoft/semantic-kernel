// Copyright (c) Microsoft. All rights reserved.

using AzureAISearchIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace AzureAISearchIntegrationTests.CRUD;

public class AzureAISearchNoVectorConformanceTests(AzureAISearchNoVectorConformanceTests.Fixture fixture)
    : NoVectorConformanceTests<string>(fixture), IClassFixture<AzureAISearchNoVectorConformanceTests.Fixture>
{
    public new class Fixture : NoVectorConformanceTests<string>.Fixture
    {
        public override string CollectionName => "novector-" + AzureAISearchTestEnvironment.TestIndexPostfix;

        public override TestStore TestStore => AzureAISearchTestStore.Instance;
    }
}
