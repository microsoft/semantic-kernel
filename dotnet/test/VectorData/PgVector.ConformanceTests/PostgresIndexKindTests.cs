// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using PgVector.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace PgVector.ConformanceTests;

public class PostgresIndexKindTests(PostgresIndexKindTests.Fixture fixture)
    : IndexKindTests<int>(fixture), IClassFixture<PostgresIndexKindTests.Fixture>
{
    [ConditionalFact]
    public virtual Task Hnsw()
        => this.Test(IndexKind.Hnsw);

    public new class Fixture() : IndexKindTests<int>.Fixture
    {
        public override TestStore TestStore => PostgresTestStore.Instance;
    }
}
