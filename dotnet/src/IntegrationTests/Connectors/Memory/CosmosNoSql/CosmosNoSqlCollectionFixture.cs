// Copyright (c) Microsoft. All rights reserved.

using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.CosmosNoSql;

[CollectionDefinition("CosmosNoSqlCollection")]
public class CosmosNoSqlCollectionFixture : ICollectionFixture<CosmosNoSqlVectorStoreFixture>
{ }
