// Copyright (c) Microsoft. All rights reserved.

using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.MongoDB;

[CollectionDefinition("MongoDBVectorStoreCollection")]
public class MongoDBVectorStoreCollectionFixture : ICollectionFixture<MongoDBVectorStoreFixture>
{ }
