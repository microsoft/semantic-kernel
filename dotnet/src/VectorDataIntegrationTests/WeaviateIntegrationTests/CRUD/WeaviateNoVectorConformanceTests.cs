// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.CRUD;
using WeaviateIntegrationTests.Support;
using Xunit;

namespace WeaviateIntegrationTests.CRUD;

public class WeaviateNoVectorConformanceTests(WeaviateNoVectorModelFixture fixture)
    : NoVectorConformanceTests<Guid>(fixture), IClassFixture<WeaviateNoVectorModelFixture>
{
}
