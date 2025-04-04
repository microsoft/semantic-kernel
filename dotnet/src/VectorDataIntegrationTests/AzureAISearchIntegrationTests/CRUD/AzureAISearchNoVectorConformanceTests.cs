// Copyright (c) Microsoft. All rights reserved.

using AzureAISearchIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace AzureAISearchIntegrationTests.CRUD;

public class AzureAISearchNoVectorConformanceTests(AzureAISearchNoVectorModelFixture fixture)
    : NoVectorConformanceTests<string>(fixture), IClassFixture<AzureAISearchNoVectorModelFixture>
{
}
