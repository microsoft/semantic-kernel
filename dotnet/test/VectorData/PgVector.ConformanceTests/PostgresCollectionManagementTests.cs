// Copyright (c) Microsoft. All rights reserved.

using PgVector.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace PgVector.ConformanceTests;

public class PostgresCollectionManagementTests(PostgresCollectionManagementTests.Fixture fixture)
    : CollectionManagementTests<string>(fixture), IClassFixture<PostgresCollectionManagementTests.Fixture>
{
    public class Fixture : VectorStoreFixture
    {
        public override TestStore TestStore => PostgresTestStore.Instance;
    }
}
