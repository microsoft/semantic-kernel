// Copyright (c) Microsoft. All rights reserved.

using InMemoryIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace InMemoryIntegrationTests.CRUD;

public class InMemoryNoVectorConformanceTests(InMemoryNoVectorModelFixture fixture)
    : NoVectorConformanceTests<string>(fixture), IClassFixture<InMemoryNoVectorModelFixture>
{
}
