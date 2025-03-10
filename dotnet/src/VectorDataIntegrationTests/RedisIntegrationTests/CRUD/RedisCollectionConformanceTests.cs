// Copyright (c) Microsoft. All rights reserved.

using RedisIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace RedisIntegrationTests.CRUD;

public class RedisCollectionConformanceTests(RedisFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<RedisFixture>
{
}
