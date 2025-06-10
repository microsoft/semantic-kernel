// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace Pinecone.ConformanceTests.Support;

public class PineconeFixture : VectorStoreFixture
{
    public override TestStore TestStore => PineconeTestStore.Instance;
}
