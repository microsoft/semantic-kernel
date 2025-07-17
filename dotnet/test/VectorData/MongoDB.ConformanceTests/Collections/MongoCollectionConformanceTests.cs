// Copyright (c) Microsoft. All rights reserved.

using MongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests.Collections;
using Xunit;

namespace MongoDB.ConformanceTests.Collections;

public class MongoCollectionConformanceTests(MongoFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<MongoFixture>
{
}
