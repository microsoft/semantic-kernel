// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace Pinecone.ConformanceTests.Support;

public class PineconeSimpleModelFixture : SimpleModelFixture<string>
{
    public override TestStore TestStore => PineconeTestStore.Instance;
}
