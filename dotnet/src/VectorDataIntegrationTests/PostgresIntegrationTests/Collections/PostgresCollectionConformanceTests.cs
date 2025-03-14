// Copyright (c) Microsoft. All rights reserved.

using PostgresIntegrationTests.Support;
using VectorDataSpecificationTests.Collections;
using Xunit;

namespace PostgresIntegrationTests.Collections;

public class PostgresCollectionConformanceTests(PostgresFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<PostgresFixture>
{
}
