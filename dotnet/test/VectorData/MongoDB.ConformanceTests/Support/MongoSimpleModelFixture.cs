// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace MongoDB.ConformanceTests.Support;

public class MongoSimpleModelFixture<TKey> : SimpleModelFixture<TKey>
    where TKey : notnull
{
    public override TestStore TestStore => MongoTestStore.Instance;
}
