// Copyright (c) Microsoft. All rights reserved.

using RedisIntegrationTests.Support;
using VectorDataSpecificationTests.Collections;
using Xunit;

namespace RedisIntegrationTests.Collections;

public class RedisJsonCollectionConformanceTests(RedisJsonFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<RedisJsonFixture>
{
}
