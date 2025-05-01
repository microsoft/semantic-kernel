// Copyright (c) Microsoft. All rights reserved.

using PostgresIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace PostgresIntegrationTests.CRUD;

public class PostgresNoVectorConformanceTests(PostgresNoVectorConformanceTests.Fixture fixture)
    : NoVectorConformanceTests<string>(fixture), IClassFixture<PostgresNoVectorConformanceTests.Fixture>
{
    public new class Fixture : NoVectorConformanceTests<string>.Fixture
    {
        public override TestStore TestStore => PostgresTestStore.Instance;
    }
}
