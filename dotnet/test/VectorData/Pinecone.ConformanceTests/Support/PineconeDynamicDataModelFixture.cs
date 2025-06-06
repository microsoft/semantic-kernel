// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace Pinecone.ConformanceTests.Support;

public class PineconeDynamicDataModelFixture : DynamicDataModelFixture<string>
{
    public override TestStore TestStore => PineconeTestStore.Instance;
}
