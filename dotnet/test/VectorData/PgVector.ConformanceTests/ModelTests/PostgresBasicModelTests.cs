// Copyright (c) Microsoft. All rights reserved.

using PgVector.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace PgVector.ConformanceTests.ModelTests;

public class PostgresBasicModelTests(PostgresBasicModelTests.Fixture fixture)
    : BasicModelTests<string>(fixture), IClassFixture<PostgresBasicModelTests.Fixture>
{
    public new class Fixture : BasicModelTests<string>.Fixture
    {
        public override TestStore TestStore => PostgresTestStore.Instance;
    }
}
