// Copyright (c) Microsoft. All rights reserved.

using SqliteVecIntegrationTests.Support;
using VectorDataSpecificationTests.VectorSearch;
using Xunit;

namespace SqliteVecIntegrationTests.VectorSearch;

public class SqliteVectorSearchWithFilterConformanceTests(SqliteFixture fixture) :
    VectorSearchWithFilterConformanceTests<string>(fixture),
    IClassFixture<SqliteFixture>
{
}
