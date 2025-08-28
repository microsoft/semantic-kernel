// Copyright (c) Microsoft. All rights reserved.

using MongoDB.Bson;
using MongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace MongoDB.ConformanceTests.CRUD;

public class MongoBatchConformanceTests_String(MongoSimpleModelFixture<string> fixture)
    : BatchConformanceTests<string>(fixture), IClassFixture<MongoSimpleModelFixture<string>>
{
}

public class MongoBatchConformanceTests_Guid(MongoSimpleModelFixture<Guid> fixture)
    : BatchConformanceTests<Guid>(fixture), IClassFixture<MongoSimpleModelFixture<Guid>>
{
}

public class MongoBatchConformanceTests_ObjectId(MongoSimpleModelFixture<ObjectId> fixture)
    : BatchConformanceTests<ObjectId>(fixture), IClassFixture<MongoSimpleModelFixture<ObjectId>>
{
}
