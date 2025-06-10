// Copyright (c) Microsoft. All rights reserved.

using AzureAISearch.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace AzureAISearch.ConformanceTests.CRUD;

public class AzureAISearchBatchConformanceTests(AzureAISearchSimpleModelFixture fixture)
    : BatchConformanceTests<string>(fixture), IClassFixture<AzureAISearchSimpleModelFixture>
{
}
