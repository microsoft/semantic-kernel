// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using SqlServer.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace SqlServer.ConformanceTests;

public class SqlServerIndexKindTests(SqlServerIndexKindTests.Fixture fixture)
    : IndexKindTests<int>(fixture), IClassFixture<SqlServerIndexKindTests.Fixture>
{
    // SQL Server 2025 currently makes tables with vector indexes read-only, so data must be inserted before
    // the index is created. See SqlServerDiskAnnVectorSearchTests for a temporary workaround test that inserts
    // data first and then creates the index. Remove the Skip and delete that class once this limitation is lifted.
    [ConditionalFact(Skip = "SQL Server 2025 read-only vector index limitation; see SqlServerDiskAnnVectorSearchTests")]
    public virtual Task DiskAnn()
        => this.Test(IndexKind.DiskAnn);

    public new class Fixture() : IndexKindTests<int>.Fixture
    {
        public override TestStore TestStore => SqlServerTestStore.Instance;
    }
}
