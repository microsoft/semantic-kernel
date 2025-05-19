// Copyright (c) Microsoft. All rights reserved.

using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.SqliteVec;

[CollectionDefinition("SqliteVectorStoreCollection")]
public class SqliteVectorStoreCollectionFixture : ICollectionFixture<SqliteVectorStoreFixture>
{ }
