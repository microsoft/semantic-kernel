// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace CosmosMongoDB.ConformanceTests.Support;

public class CosmosMongoSimpleModelFixture : SimpleModelFixture<string>
{
    public override TestStore TestStore => CosmosMongoTestStore.Instance;
}
