// Copyright (c) Microsoft. All rights reserved.

using InMemoryIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace InMemoryIntegrationTests.CRUD;

public class InMemoryNoDataConformanceTests(InMemoryNoDataConformanceTests.Fixture fixture)
    : NoDataConformanceTests<string>(fixture), IClassFixture<InMemoryNoDataConformanceTests.Fixture>
{
    public new class Fixture : NoDataConformanceTests<string>.Fixture
    {
        public override TestStore TestStore => InMemoryTestStore.Instance;
    }
}
