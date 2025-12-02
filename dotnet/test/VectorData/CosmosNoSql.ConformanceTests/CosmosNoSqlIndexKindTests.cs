// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSql.ConformanceTests.Support;
using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace CosmosNoSql.ConformanceTests;

public class CosmosNoSqlIndexKindTests(CosmosNoSqlIndexKindTests.Fixture fixture)
    : IndexKindTests<string>(fixture), IClassFixture<CosmosNoSqlIndexKindTests.Fixture>
{
    [ConditionalFact(Skip = "DiskANN is supported by Cosmos NoSQL, but is not supported on the emulator and needs to be explicitly enabled")]
    public virtual Task DiskANN()
        => this.Test(IndexKind.DiskAnn);

    public new class Fixture() : IndexKindTests<string>.Fixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
    }
}
