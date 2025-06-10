// Copyright (c) Microsoft. All rights reserved.

using Redis.ConformanceTests.Support;
using VectorData.ConformanceTests.Collections;
using Xunit;

namespace Redis.ConformanceTests.Collections;

public class RedisJsonCollectionConformanceTests(RedisJsonFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<RedisJsonFixture>
{
}
