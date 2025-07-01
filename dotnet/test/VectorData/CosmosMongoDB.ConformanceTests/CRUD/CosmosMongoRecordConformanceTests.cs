// Copyright (c) Microsoft. All rights reserved.

using CosmosMongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace CosmosMongoDB.ConformanceTests.CRUD;

public class CosmosMongoRecordConformanceTests(CosmosMongoSimpleModelFixture fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<CosmosMongoSimpleModelFixture>
{
}
