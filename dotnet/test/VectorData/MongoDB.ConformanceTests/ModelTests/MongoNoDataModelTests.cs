// Copyright (c) Microsoft. All rights reserved.

using MongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace MongoDB.ConformanceTests.ModelTests;

public class MongoNoDataModelTests(MongoNoDataModelTests.Fixture fixture)
    : NoDataModelTests<string>(fixture), IClassFixture<MongoNoDataModelTests.Fixture>
{
    public new class Fixture : NoDataModelTests<string>.Fixture
    {
        public override TestStore TestStore => MongoTestStore.Instance;
    }
}
