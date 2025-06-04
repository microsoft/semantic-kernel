// Copyright (c) Microsoft. All rights reserved.

using PgVectorIntegrationTests.Support;

namespace PgVectorIntegrationTests.VectorSearch;

public class PostgresVectorSearchDistanceFunctionComplianceTests_Hnsw(PostgresFixture fixture) : PostgresVectorSearchDistanceFunctionComplianceTests(fixture)
{
    protected override string IndexKind => Microsoft.Extensions.VectorData.IndexKind.Hnsw;
}
