// Copyright (c) Microsoft. All rights reserved.

using SqlServer.ConformanceTests.Support;
using VectorData.ConformanceTests.Filter;
using VectorData.ConformanceTests.Support;
using Xunit;
using Xunit.Sdk;

namespace SqlServer.ConformanceTests.Filter;

#pragma warning disable CS0252 // Possible unintended reference comparison; left hand side needs cast

public class SqlServerBasicFilterTests(SqlServerBasicFilterTests.Fixture fixture)
    : BasicFilterTests<int>(fixture), IClassFixture<SqlServerBasicFilterTests.Fixture>
{
    public override async Task Not_over_Or()
    {
        // Test sends: WHERE (NOT (("Int" = 8) OR ("String" = 'foo')))
        // There's a NULL string in the database, and relational null semantics in conjunction with negation makes the default implementation fail.
        await Assert.ThrowsAsync<FailException>(() => base.Not_over_Or());

        // Compensate by adding a null check:
        await this.TestFilterAsync(
            r => r.String != null && !(r.Int == 8 || r.String == "foo"),
            r => r["String"] != null && !((int)r["Int"]! == 8 || r["String"] == "foo"));
    }

    public override async Task NotEqual_with_string()
    {
        // As above, null semantics + negation
        await Assert.ThrowsAsync<FailException>(() => base.NotEqual_with_string());

        await this.TestFilterAsync(
            r => r.String != null && r.String != "foo",
            r => r["String"] != null && r["String"] != "foo");
    }

    [Fact(Skip = "Not supported")]
    [Obsolete("Legacy filters are not supported")]
    public override Task Legacy_And() => throw new NotSupportedException();

    [Fact(Skip = "Not supported")]
    [Obsolete("Legacy filters are not supported")]
    public override Task Legacy_AnyTagEqualTo_array() => throw new NotSupportedException();

    [Fact(Skip = "Not supported")]
    [Obsolete("Legacy filters are not supported")]
    public override Task Legacy_AnyTagEqualTo_List() => throw new NotSupportedException();

    [Fact(Skip = "Not supported")]
    [Obsolete("Legacy filters are not supported")]
    public override Task Legacy_equality() => throw new NotSupportedException();

    public new class Fixture : BasicFilterTests<int>.Fixture
    {
        private static readonly string s_uniqueName = Guid.NewGuid().ToString();

        public override TestStore TestStore => SqlServerTestStore.Instance;

        public override string CollectionName => s_uniqueName;
    }
}
