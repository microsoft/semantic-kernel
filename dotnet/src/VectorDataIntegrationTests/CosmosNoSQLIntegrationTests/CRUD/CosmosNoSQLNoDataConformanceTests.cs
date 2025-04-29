// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSQLIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace CosmosNoSQLIntegrationTests.CRUD;

public class CosmosNoSQLNoDataConformanceTests(CosmosNoSQLNoDataConformanceTests.Fixture fixture)
    : NoDataConformanceTests<string>(fixture), IClassFixture<CosmosNoSQLNoDataConformanceTests.Fixture>
{
    public new class Fixture : NoDataConformanceTests<string>.Fixture
    {
        public override TestStore TestStore => CosmosNoSQLTestStore.Instance;
    }
}
