// Copyright (c) Microsoft. All rights reserved.

using SqliteIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace SqliteIntegrationTests.CRUD;

public class SqliteNoVectorConformanceTests(SqliteNoVectorConformanceTests.Fixture fixture)
    : NoVectorConformanceTests<string>(fixture), IClassFixture<SqliteNoVectorConformanceTests.Fixture>
{
    public new class Fixture : NoVectorConformanceTests<string>.Fixture
    {
        public override TestStore TestStore => SqliteTestStore.Instance;
    }
}
