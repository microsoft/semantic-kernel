// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace SqliteVec.ConformanceTests.Support;

public class SqliteSimpleModelFixture<TKey> : SimpleModelFixture<TKey>
    where TKey : notnull
{
    public override TestStore TestStore => SqliteTestStore.Instance;
}
