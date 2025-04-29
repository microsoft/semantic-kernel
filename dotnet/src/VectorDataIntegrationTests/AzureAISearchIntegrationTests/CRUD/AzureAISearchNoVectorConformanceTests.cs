// Copyright (c) Microsoft. All rights reserved.

using System.Text.RegularExpressions;
using AzureAISearchIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace AzureAISearchIntegrationTests.CRUD;

public class AzureAISearchNoVectorConformanceTests(AzureAISearchNoVectorConformanceTests.Fixture fixture)
    : NoVectorConformanceTests<string>(fixture), IClassFixture<AzureAISearchNoVectorConformanceTests.Fixture>
{
#pragma warning disable CA1308 // Normalize strings to uppercase
    private static readonly string _testIndexPostfix = new Regex("[^a-zA-Z0-9]").Replace(Environment.MachineName.ToLowerInvariant(), "");
#pragma warning restore CA1308 // Normalize strings to uppercase

    public new class Fixture : NoVectorConformanceTests<string>.Fixture
    {
        public override string CollectionName => "novector-" + _testIndexPostfix;

        public override TestStore TestStore => AzureAISearchTestStore.Instance;
    }
}
