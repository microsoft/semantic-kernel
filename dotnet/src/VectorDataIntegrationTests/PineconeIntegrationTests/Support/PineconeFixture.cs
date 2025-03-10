// Copyright (c) Microsoft. All rights reserved.

using Pinecone;
using VectorDataSpecificationTests.Support;

namespace PineconeIntegrationTests.Support;

public class PineconeFixture : VectorStoreFixture
{
    public override TestStore TestStore => PineconeTestStore.Instance;

    public PineconeClient Client => PineconeTestStore.Instance.Client;
}
