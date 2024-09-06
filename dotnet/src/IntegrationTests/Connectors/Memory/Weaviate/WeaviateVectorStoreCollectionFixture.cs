// Copyright (c) Microsoft. All rights reserved.

using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Weaviate;

[CollectionDefinition("WeaviateVectorStoreCollection")]
public class WeaviateVectorStoreCollectionFixture : ICollectionFixture<WeaviateVectorStoreFixture>
{ }
