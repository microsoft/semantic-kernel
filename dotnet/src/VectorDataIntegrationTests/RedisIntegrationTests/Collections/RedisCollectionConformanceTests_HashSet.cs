// Copyright (c) Microsoft. All rights reserved.

using RedisIntegrationTests.Support;
using VectorDataSpecificationTests.Collections;
using Xunit;

namespace RedisIntegrationTests.Collections;

public class RedisCollectionConformanceTests_HashSet(RedisHashSetFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<RedisHashSetFixture>
{
}
