// Copyright (c) Microsoft. All rights reserved.

using AzureAISearch.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace AzureAISearch.ConformanceTests.CRUD;

public class AzureAISearchRecordConformanceTests(AzureAISearchSimpleModelFixture fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<AzureAISearchSimpleModelFixture>
{
}
