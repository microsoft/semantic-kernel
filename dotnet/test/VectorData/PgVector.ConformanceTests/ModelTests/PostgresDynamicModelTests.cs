// Copyright (c) Microsoft. All rights reserved.

using PgVector.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace PgVector.ConformanceTests.ModelTests;

public class PostgresDynamicModelTests(PostgresDynamicModelTests.Fixture fixture)
    : DynamicModelTests<string>(fixture), IClassFixture<PostgresDynamicModelTests.Fixture>
{
    public new class Fixture : DynamicModelTests<string>.Fixture
    {
        public override TestStore TestStore => PostgresTestStore.Instance;
    }
}
