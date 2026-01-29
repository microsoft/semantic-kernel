// Copyright (c) Microsoft. All rights reserved.

using SqliteVec.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace SqliteVec.ConformanceTests.ModelTests;

public class SqliteMultiVectorModelTests(SqliteMultiVectorModelTests.Fixture fixture)
    : MultiVectorModelTests<string>(fixture), IClassFixture<SqliteMultiVectorModelTests.Fixture>
{
    public new class Fixture : MultiVectorModelTests<string>.Fixture
    {
        public override TestStore TestStore => SqliteTestStore.Instance;
    }
}
