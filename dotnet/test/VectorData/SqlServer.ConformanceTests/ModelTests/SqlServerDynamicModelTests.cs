// Copyright (c) Microsoft. All rights reserved.

using SqlServer.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace SqlServer.ConformanceTests.ModelTests;

public class SqlServerDynamicModelTests(SqlServerDynamicModelTests.Fixture fixture)
    : DynamicModelTests<string>(fixture), IClassFixture<SqlServerDynamicModelTests.Fixture>
{
    public new class Fixture : DynamicModelTests<string>.Fixture
    {
        public override TestStore TestStore => SqlServerTestStore.Instance;
    }
}
