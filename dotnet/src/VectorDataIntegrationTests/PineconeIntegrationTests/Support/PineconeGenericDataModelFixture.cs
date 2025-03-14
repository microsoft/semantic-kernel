// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace PineconeIntegrationTests.Support;

public class PineconeGenericDataModelFixture : GenericDataModelFixture<string>
{
    public override TestStore TestStore => PineconeTestStore.Instance;
}
