// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace SqliteVec.ConformanceTests.Support;

public class SqliteFixture : VectorStoreFixture
{
    public override TestStore TestStore => SqliteTestStore.Instance;
}
