// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.CosmosNoSql;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.CosmosNoSql;

/// <summary>
/// Integration tests for <see cref="CosmosNoSqlVectorStore"/>.
/// </summary>
[Collection("CosmosNoSqlVectorStoreCollection")]
[CosmosNoSqlConnectionStringSetCondition]
public sealed class CosmosNoSqlVectorStoreTests(CosmosNoSqlVectorStoreFixture fixture)
    : BaseVectorStoreTests<string, CosmosNoSqlHotel>(new CosmosNoSqlVectorStore(fixture.Database!))
{
}
