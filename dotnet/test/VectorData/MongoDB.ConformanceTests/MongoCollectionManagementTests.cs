// Copyright (c) Microsoft. All rights reserved.

using MongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests;
using Xunit;

namespace MongoDB.ConformanceTests;

public class MongoCollectionManagementTests(MongoFixture fixture)
    : CollectionManagementTests<string>(fixture), IClassFixture<MongoFixture>
{
}
