// Copyright (c) Microsoft. All rights reserved.

using WeaviateIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace WeaviateIntegrationTests.CRUD;

public class WeaviateNoVectorConformanceTests(WeaviateNoVectorModelFixture fixture)
    : NoVectorConformanceTests<Guid>(fixture), IClassFixture<WeaviateNoVectorModelFixture>
{
}
