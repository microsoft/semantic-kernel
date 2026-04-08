// Copyright (c) Microsoft. All rights reserved.

using PgVector.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace PgVector.ConformanceTests.ModelTests;

public class PostgresMultiVectorModelTests(PostgresMultiVectorModelTests.Fixture fixture)
    : MultiVectorModelTests<string>(fixture), IClassFixture<PostgresMultiVectorModelTests.Fixture>
{
    public new class Fixture : MultiVectorModelTests<string>.Fixture
    {
        public override TestStore TestStore => PostgresTestStore.Instance;
    }
}
