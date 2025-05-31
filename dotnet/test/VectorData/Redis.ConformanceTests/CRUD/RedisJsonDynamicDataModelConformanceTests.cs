// Copyright (c) Microsoft. All rights reserved.

using RedisIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace RedisIntegrationTests.CRUD;

public class RedisJsonDynamicDataModelConformanceTests(RedisJsonDynamicDataModelFixture fixture)
    : DynamicDataModelConformanceTests<string>(fixture), IClassFixture<RedisJsonDynamicDataModelFixture>
{
}
