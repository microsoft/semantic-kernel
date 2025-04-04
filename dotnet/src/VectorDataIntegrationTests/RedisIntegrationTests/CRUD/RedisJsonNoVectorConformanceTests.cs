// Copyright (c) Microsoft. All rights reserved.

using RedisIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace RedisIntegrationTests.CRUD;

public class RedisJsonNoVectorConformanceTests(RedisJsonNoVectorModelFixture fixture)
    : NoVectorConformanceTests<string>(fixture), IClassFixture<RedisJsonNoVectorModelFixture>
{
}
