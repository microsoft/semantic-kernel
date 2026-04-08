// Copyright (c) Microsoft. All rights reserved.

using PgVector.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace PgVector.ConformanceTests.ModelTests;

public class PostgresNoVectorModelTests(PostgresNoVectorModelTests.Fixture fixture)
    : NoVectorModelTests<string>(fixture), IClassFixture<PostgresNoVectorModelTests.Fixture>
{
    public new class Fixture : NoVectorModelTests<string>.Fixture
    {
        public override TestStore TestStore => PostgresTestStore.Instance;
    }
}
