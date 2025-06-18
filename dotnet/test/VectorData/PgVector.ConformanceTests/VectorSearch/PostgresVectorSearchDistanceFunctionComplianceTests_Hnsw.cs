// Copyright (c) Microsoft. All rights reserved.

using PgVector.ConformanceTests.Support;

namespace PgVector.ConformanceTests.VectorSearch;

public class PostgresVectorSearchDistanceFunctionComplianceTests_Hnsw(PostgresFixture fixture) : PostgresVectorSearchDistanceFunctionComplianceTests(fixture)
{
    protected override string IndexKind => Microsoft.Extensions.VectorData.IndexKind.Hnsw;
}
