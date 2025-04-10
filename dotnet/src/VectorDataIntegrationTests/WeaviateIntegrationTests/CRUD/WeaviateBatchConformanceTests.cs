// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.CRUD;
using WeaviateIntegrationTests.Support;
using Xunit;

namespace WeaviateIntegrationTests.CRUD;

public class WeaviateBatchConformanceTests(WeaviateSimpleModelFixture fixture)
    : BatchConformanceTests<Guid>(fixture), IClassFixture<WeaviateSimpleModelFixture>
{
}
