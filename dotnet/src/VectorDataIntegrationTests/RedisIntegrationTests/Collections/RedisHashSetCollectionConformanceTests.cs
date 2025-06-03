// Copyright (c) Microsoft. All rights reserved.

using RedisIntegrationTests.Support;
using VectorDataSpecificationTests.Collections;
using Xunit;

namespace RedisIntegrationTests.Collections;

public class RedisHashSetCollectionConformanceTests(RedisHashSetFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<RedisHashSetFixture>
{
}
