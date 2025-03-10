// Copyright (c) Microsoft. All rights reserved.

using PostgresIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace PostgresIntegrationTests.CRUD;

public class PostgresCollectionConformanceTests(PostgresFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<PostgresFixture>
{
}
