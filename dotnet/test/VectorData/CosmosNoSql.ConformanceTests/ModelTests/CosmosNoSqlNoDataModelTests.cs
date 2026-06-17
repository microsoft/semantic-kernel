// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSql.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace CosmosNoSql.ConformanceTests.ModelTests;

public class CosmosNoSqlNoDataModelTests(CosmosNoSqlNoDataModelTests.Fixture fixture)
    : NoDataModelTests<string>(fixture), IClassFixture<CosmosNoSqlNoDataModelTests.Fixture>
{
    public new class Fixture : NoDataModelTests<string>.Fixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
    }
}
