// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace PgVector.ConformanceTests.Support;

public class PostgresSimpleModelFixture : SimpleModelFixture<string>
{
    public override TestStore TestStore => PostgresTestStore.Instance;
}
