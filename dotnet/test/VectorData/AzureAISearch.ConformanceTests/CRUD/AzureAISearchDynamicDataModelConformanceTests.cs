// Copyright (c) Microsoft. All rights reserved.

using AzureAISearch.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace AzureAISearch.ConformanceTests.CRUD;

public class AzureAISearchDynamicDataModelConformanceTests(AzureAISearchDynamicDataModelFixture fixture)
    : DynamicDataModelConformanceTests<string>(fixture), IClassFixture<AzureAISearchDynamicDataModelFixture>
{
}
