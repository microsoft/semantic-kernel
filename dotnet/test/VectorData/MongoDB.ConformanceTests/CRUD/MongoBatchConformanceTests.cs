// Copyright (c) Microsoft. All rights reserved.

using MongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace MongoDB.ConformanceTests.CRUD;

public class MongoBatchConformanceTests(MongoSimpleModelFixture fixture)
    : BatchConformanceTests<string>(fixture), IClassFixture<MongoSimpleModelFixture>
{
}
