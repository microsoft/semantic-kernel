// Copyright (c) Microsoft. All rights reserved.

using AzureAISearchIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace AzureAISearchIntegrationTests.CRUD;

public class AzureAISearchRecordConformanceTests(AzureAISearchSimpleModelFixture fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<AzureAISearchSimpleModelFixture>
{
}
