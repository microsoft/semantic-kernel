// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace SqliteIntegrationTests.Support;

public class SqliteSimpleModelFixture<TKey> : SimpleModelFixture<TKey>
    where TKey : notnull
{
    public override TestStore TestStore => SqliteTestStore.Instance;
}
