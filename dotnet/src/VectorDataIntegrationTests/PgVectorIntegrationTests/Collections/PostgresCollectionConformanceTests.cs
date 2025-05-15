// Copyright (c) Microsoft. All rights reserved.

using PgVectorIntegrationTests.Support;
using VectorDataSpecificationTests.Collections;
using Xunit;

namespace PgVectorIntegrationTests.Collections;

public class PostgresCollectionConformanceTests(PostgresFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<PostgresFixture>
{
}
