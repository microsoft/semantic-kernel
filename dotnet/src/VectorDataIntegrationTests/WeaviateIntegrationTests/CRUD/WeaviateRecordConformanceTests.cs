// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.CRUD;
using WeaviateIntegrationTests.Support;
using Xunit;

namespace WeaviateIntegrationTests.CRUD;

public class WeaviateRecordConformanceTests(WeaviateSimpleModelFixture fixture)
    : RecordConformanceTests<Guid>(fixture), IClassFixture<WeaviateSimpleModelFixture>
{
}
