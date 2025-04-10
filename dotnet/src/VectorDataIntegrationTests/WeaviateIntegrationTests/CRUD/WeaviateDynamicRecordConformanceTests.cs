// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.CRUD;
using WeaviateIntegrationTests.Support;
using Xunit;

namespace WeaviateIntegrationTests.CRUD;

public class WeaviateDynamicRecordConformanceTests(WeaviateDynamicDataModelFixture fixture)
    : DynamicDataModelConformanceTests<Guid>(fixture), IClassFixture<WeaviateDynamicDataModelFixture>
{
}
