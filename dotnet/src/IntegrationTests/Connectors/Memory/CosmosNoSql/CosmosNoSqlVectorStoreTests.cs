// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.CosmosNoSql;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.CosmosNoSql;

/// <summary>
/// Integration tests for <see cref="CosmosNoSqlVectorStore"/>.
/// </summary>
[Collection("CosmosNoSqlCollection")]
[CosmosNoSqlConnectionStringSetCondition]
public sealed class CosmosNoSqlVectorStoreTests(CosmosNoSqlVectorStoreFixture fixture)
#pragma warning disable CA2000 // Dispose objects before losing scope
    : BaseVectorStoreTests<string, CosmosNoSqlHotel>(new CosmosNoSqlVectorStore(fixture.Database!))
#pragma warning restore CA2000 // Dispose objects before losing scope
{
}
