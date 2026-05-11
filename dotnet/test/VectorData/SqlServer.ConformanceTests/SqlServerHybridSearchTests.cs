// Copyright (c) Microsoft. All rights reserved.

using SqlServer.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace SqlServer.ConformanceTests;

public class SqlServerHybridSearchTests(
    SqlServerHybridSearchTests.VectorAndStringFixture vectorAndStringFixture,
    SqlServerHybridSearchTests.MultiTextFixture multiTextFixture)
    : HybridSearchTests<int>(vectorAndStringFixture, multiTextFixture),
        IClassFixture<SqlServerHybridSearchTests.VectorAndStringFixture>,
        IClassFixture<SqlServerHybridSearchTests.MultiTextFixture>
{
    public new class VectorAndStringFixture : HybridSearchTests<int>.VectorAndStringFixture
    {
        public override TestStore TestStore => SqlServerTestStore.Instance;
    }

    public new class MultiTextFixture : HybridSearchTests<int>.MultiTextFixture
    {
        public override TestStore TestStore => SqlServerTestStore.Instance;
    }
}
