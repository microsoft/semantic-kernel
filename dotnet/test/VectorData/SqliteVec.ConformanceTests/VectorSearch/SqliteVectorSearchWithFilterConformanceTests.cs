// Copyright (c) Microsoft. All rights reserved.

using SqliteVec.ConformanceTests.Support;
using VectorData.ConformanceTests.VectorSearch;
using Xunit;

namespace SqliteVec.ConformanceTests.VectorSearch;

public class SqliteVectorSearchWithFilterConformanceTests(SqliteFixture fixture) :
    VectorSearchWithFilterConformanceTests<string>(fixture),
    IClassFixture<SqliteFixture>
{
}
