// Copyright (c) Microsoft. All rights reserved.

using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Sqlite;

[CollectionDefinition("SqliteVectorStoreCollection")]
public class SqliteVectorStoreCollectionFixture : ICollectionFixture<SqliteVectorStoreFixture>
{ }
