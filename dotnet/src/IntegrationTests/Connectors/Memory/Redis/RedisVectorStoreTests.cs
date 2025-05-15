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
#pragma warning disable CA2000 // Dispose objects before losing scope
    : BaseVectorStoreTests<string, RedisHotel>(new RedisVectorStore(fixture.Database))
#pragma warning restore CA2000 // Dispose objects before losing scope
{
}
