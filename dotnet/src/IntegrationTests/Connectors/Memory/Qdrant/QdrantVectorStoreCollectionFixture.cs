// Copyright (c) Microsoft. All rights reserved.

using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Qdrant;

[CollectionDefinition("QdrantVectorStoreCollection")]
public class QdrantVectorStoreCollectionFixture : ICollectionFixture<QdrantVectorStoreFixture>
{
}
