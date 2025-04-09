// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.Redis;
using SemanticKernel.IntegrationTests.Connectors.Memory.Xunit;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Redis;

/// <summary>
/// Contains tests for the <see cref="RedisVectorStore"/> class.
/// </summary>
/// <param name="fixture">The test fixture.</param>
[Collection("RedisVectorStoreCollection")]
[DisableVectorStoreTests(Skip = "Redis tests fail intermittently on build server")]
public class RedisVectorStoreTests(RedisVectorStoreFixture fixture)
    : BaseVectorStoreTests<string, RedisHotel>(new RedisVectorStore(fixture.Database))
{
}
