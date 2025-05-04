﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureCosmosDBNoSQL;

/// <summary>
/// Integration tests for <see cref="CosmosNoSqlVectorStore"/>.
/// </summary>
[Collection("AzureCosmosDBNoSQLVectorStoreCollection")]
[AzureCosmosDBNoSQLConnectionStringSetCondition]
public sealed class AzureCosmosDBNoSQLVectorStoreTests(AzureCosmosDBNoSQLVectorStoreFixture fixture)
    : BaseVectorStoreTests<string, AzureCosmosDBNoSQLHotel>(new CosmosNoSqlVectorStore(fixture.Database!))
{
}
