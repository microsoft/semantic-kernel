// Copyright (c) Microsoft. All rights reserved.

using Redis.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace Redis.ConformanceTests.CRUD;

public class RedisJsonRecordConformanceTests(RedisJsonSimpleModelFixture fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<RedisJsonSimpleModelFixture>
{
}
