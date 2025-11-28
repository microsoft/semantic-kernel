// Copyright (c) Microsoft. All rights reserved.

using SqlServer.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace SqlServer.ConformanceTests;

public class SqlServerIndexKindTests(SqlServerIndexKindTests.Fixture fixture)
    : IndexKindTests<int>(fixture), IClassFixture<SqlServerIndexKindTests.Fixture>
{
    public new class Fixture() : IndexKindTests<int>.Fixture
    {
        public override TestStore TestStore => SqlServerTestStore.Instance;
    }
}
