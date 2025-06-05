// Copyright (c) Microsoft. All rights reserved.

using PgVector.ConformanceTests.Support;
using VectorData.ConformanceTests.Collections;
using Xunit;

namespace PgVector.ConformanceTests.Collections;

public class PostgresCollectionConformanceTests(PostgresFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<PostgresFixture>
{
}
