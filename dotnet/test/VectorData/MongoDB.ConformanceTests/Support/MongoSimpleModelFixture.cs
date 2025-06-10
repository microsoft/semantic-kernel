// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace MongoDB.ConformanceTests.Support;

public class MongoSimpleModelFixture : SimpleModelFixture<string>
{
    public override TestStore TestStore => MongoTestStore.Instance;
}
