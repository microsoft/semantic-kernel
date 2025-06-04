// Copyright (c) Microsoft. All rights reserved.

using AzureAISearchIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace AzureAISearchIntegrationTests.CRUD;

public class AzureAISearchDynamicDataModelConformanceTests(AzureAISearchDynamicDataModelFixture fixture)
    : DynamicDataModelConformanceTests<string>(fixture), IClassFixture<AzureAISearchDynamicDataModelFixture>
{
}
