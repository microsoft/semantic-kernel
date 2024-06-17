// Copyright (c) Microsoft. All rights reserved.

using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Redis;

[CollectionDefinition("RedisVectorStoreCollection")]
public class RedisVectorStoreCollectionFixture : ICollectionFixture<RedisVectorStoreFixture>
{
}
