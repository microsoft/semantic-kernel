// Copyright (c) Microsoft. All rights reserved.

using RedisIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace RedisIntegrationTests.CRUD;

public class RedisHashSetRecordConformanceTests(RedisHashSetSimpleModelFixture fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<RedisHashSetSimpleModelFixture>
{
}
