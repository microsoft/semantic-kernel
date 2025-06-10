// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace PgVector.ConformanceTests.Support;

public class PostgresFixture : VectorStoreFixture
{
    public override TestStore TestStore => PostgresTestStore.Instance;
}
