// Copyright (c) Microsoft. All rights reserved.

using SqliteVecIntegrationTests.Support;
using VectorDataSpecificationTests.Collections;
using Xunit;

namespace SqliteVecIntegrationTests.Collections;

public class SqliteCollectionConformanceTests(SqliteFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<SqliteFixture>
{
}
