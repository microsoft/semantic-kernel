// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace PineconeIntegrationTests.Support;

public class PineconeFixture : VectorStoreFixture
{
    public override TestStore TestStore => PineconeTestStore.Instance;
}
