// Copyright (c) Microsoft. All rights reserved.

using PgVector.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace PgVector.ConformanceTests.ModelTests;

public class PostgresNoDataModelTests(PostgresNoDataModelTests.Fixture fixture)
    : NoDataModelTests<string>(fixture), IClassFixture<PostgresNoDataModelTests.Fixture>
{
    public new class Fixture : NoDataModelTests<string>.Fixture
    {
        public override TestStore TestStore => PostgresTestStore.Instance;
    }
}
