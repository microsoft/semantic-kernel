// Copyright (c) Microsoft. All rights reserved.

using SqliteVec.ConformanceTests.Support;
using VectorData.ConformanceTests.Collections;
using Xunit;

namespace SqliteVec.ConformanceTests.Collections;

public class SqliteCollectionConformanceTests(SqliteFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<SqliteFixture>
{
}
