// Copyright (c) Microsoft. All rights reserved.

using Redis.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace Redis.ConformanceTests.CRUD;

public class RedisHashSetDynamicDataModelConformanceTests(RedisHashSetDynamicDataModelFixture fixture)
    : DynamicDataModelConformanceTests<string>(fixture), IClassFixture<RedisHashSetDynamicDataModelFixture>
{
}
