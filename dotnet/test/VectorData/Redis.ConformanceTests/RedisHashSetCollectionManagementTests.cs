// Copyright (c) Microsoft. All rights reserved.

using Redis.ConformanceTests.Support;
using VectorData.ConformanceTests;
using Xunit;

namespace Redis.ConformanceTests;

public class RedisHashSetCollectionManagementTests(RedisHashSetFixture fixture)
    : CollectionManagementTests<string>(fixture), IClassFixture<RedisHashSetFixture>
{
}
