// Copyright (c) Microsoft. All rights reserved.

using AzureAISearchIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace AzureAISearchIntegrationTests.CRUD;

public class AzureAISearchBatchConformanceTests(AzureAISearchSimpleModelFixture fixture)
    : BatchConformanceTests<string>(fixture), IClassFixture<AzureAISearchSimpleModelFixture>
{
}
