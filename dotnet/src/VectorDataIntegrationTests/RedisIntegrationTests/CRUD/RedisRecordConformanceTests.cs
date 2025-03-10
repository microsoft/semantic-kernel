// Copyright (c) Microsoft. All rights reserved.

using RedisIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace RedisIntegrationTests.CRUD;

public class RedisRecordConformanceTests(RedisFixture fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<RedisFixture>
{
}
