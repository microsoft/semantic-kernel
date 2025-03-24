// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace MongoDBIntegrationTests.Support;

public class MongoDBFixture : VectorStoreFixture
{
    public override TestStore TestStore => MongoDBTestStore.Instance;
}
