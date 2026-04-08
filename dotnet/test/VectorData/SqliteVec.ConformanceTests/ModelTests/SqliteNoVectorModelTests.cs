// Copyright (c) Microsoft. All rights reserved.

using SqliteVec.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace SqliteVec.ConformanceTests.ModelTests;

public class SqliteNoVectorModelTests(SqliteNoVectorModelTests.Fixture fixture)
    : NoVectorModelTests<string>(fixture), IClassFixture<SqliteNoVectorModelTests.Fixture>
{
    public new class Fixture : NoVectorModelTests<string>.Fixture
    {
        public override TestStore TestStore => SqliteTestStore.Instance;
    }
}
