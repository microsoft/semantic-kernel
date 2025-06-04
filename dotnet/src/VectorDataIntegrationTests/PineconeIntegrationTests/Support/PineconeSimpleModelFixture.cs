// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace PineconeIntegrationTests.Support;

public class PineconeSimpleModelFixture : SimpleModelFixture<string>
{
    public override TestStore TestStore => PineconeTestStore.Instance;
}
