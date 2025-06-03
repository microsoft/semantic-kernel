// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace PineconeIntegrationTests.Support;

public class PineconeDynamicDataModelFixture : DynamicDataModelFixture<string>
{
    public override TestStore TestStore => PineconeTestStore.Instance;
}
