// Copyright (c) Microsoft. All rights reserved.

using MongoDBIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace MongoDBIntegrationTests.CRUD;

public class MongoDBRecordConformanceTests(MongoDBSimpleModelFixture fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<MongoDBSimpleModelFixture>
{
}
