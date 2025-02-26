// Copyright (c) Microsoft. All rights reserved.

using PostgresIntegrationTests.Support;

namespace PostgresIntegrationTests.VectorSearch;

public class PostgresBasicVectorSearchTests_Hnsw(PostgresFixture fixture) : PostgresBasicVectorSearchTests(fixture)
{
    protected override string IndexKind => Microsoft.Extensions.VectorData.IndexKind.Hnsw;
}
