// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace MongoDBIntegrationTests.Support;

public class MongoDBNoVectorModelFixture : NoVectorModelFixture<string>
{
    public override TestStore TestStore => MongoDBTestStore.Instance;
}
