// Copyright (c) Microsoft. All rights reserved.

using RedisIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace RedisIntegrationTests.CRUD;

public class RedisRecordConformanceTests(RedisSimpleModelFixture fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<RedisSimpleModelFixture>
{
}
