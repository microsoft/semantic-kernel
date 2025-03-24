// Copyright (c) Microsoft. All rights reserved.

using RedisIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace RedisIntegrationTests.CRUD;

public class RedisGenericDataModelConformanceTests(RedisGenericDataModelFixture fixture)
    : GenericDataModelConformanceTests<string>(fixture), IClassFixture<RedisGenericDataModelFixture>
{
}
