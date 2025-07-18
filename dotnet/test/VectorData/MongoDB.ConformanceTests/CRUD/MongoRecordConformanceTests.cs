// Copyright (c) Microsoft. All rights reserved.

using MongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace MongoDB.ConformanceTests.CRUD;

public class MongoRecordConformanceTests(MongoSimpleModelFixture fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<MongoSimpleModelFixture>
{
}
