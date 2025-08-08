// Copyright (c) Microsoft. All rights reserved.

using MongoDB.Bson;
using MongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace MongoDB.ConformanceTests.CRUD;

public class MongoRecordConformanceTests_String(MongoSimpleModelFixture<string> fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<MongoSimpleModelFixture<string>>
{
}

public class MongoRecordConformanceTests_Guid(MongoSimpleModelFixture<Guid> fixture)
    : RecordConformanceTests<Guid>(fixture), IClassFixture<MongoSimpleModelFixture<Guid>>
{
}

public class MongoRecordConformanceTests_ObjectId(MongoSimpleModelFixture<ObjectId> fixture)
    : RecordConformanceTests<ObjectId>(fixture), IClassFixture<MongoSimpleModelFixture<ObjectId>>
{
}
