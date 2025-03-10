// Copyright (c) Microsoft. All rights reserved.

using PostgresIntegrationTests.Support;

namespace PostgresIntegrationTests.VectorSearch;

public class PostgresVectorSearchDistanceFunctionComplianceTests_Hnsw(PostgresFixture fixture) : PostgresVectorSearchDistanceFunctionComplianceTests(fixture)
{
    protected override string IndexKind => Microsoft.Extensions.VectorData.IndexKind.Hnsw;
}
