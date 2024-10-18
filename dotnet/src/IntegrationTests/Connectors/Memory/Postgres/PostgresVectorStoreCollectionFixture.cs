// Copyright (c) Microsoft. All rights reserved.

using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Postgres;

[CollectionDefinition("PostgresVectorStoreCollection")]
public class PostgresVectorStoreCollectionFixture : ICollectionFixture<PostgresVectorStoreFixture>
{
}
