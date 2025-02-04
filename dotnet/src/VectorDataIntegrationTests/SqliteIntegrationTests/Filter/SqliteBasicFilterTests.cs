// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Filter;
using SqliteIntegrationTests.Support;
using Xunit;
using Xunit.Sdk;

namespace SqliteIntegrationTests.Filter;

public class SqliteBasicFilterTests(SqliteFilterFixture fixture) : BasicFilterTestsBase<ulong>(fixture), IClassFixture<SqliteFilterFixture>
{
    public override async Task Not_over_Or()
    {
        // Test sends: WHERE (NOT (("Int" = 8) OR ("String" = 'foo')))
        // There's a NULL string in the database, and relational null semantics in conjunction with negation makes the default implementation fail.
        await Assert.ThrowsAsync<EqualException>(() => base.Not_over_Or());

        // Compensate by adding a null check:
        await this.TestFilter(r => r.String != null && !(r.Int == 8 || r.String == "foo"));
    }

    public override async Task NotEqual_with_string()
    {
        // As above, null semantics + negation
        await Assert.ThrowsAsync<EqualException>(() => base.NotEqual_with_string());

        await this.TestFilter(r => r.String != null && r.String != "foo");
    }

    // Array fields not (currently)s upported on SQLite (see #10343)
    public override Task Contains_over_field_string_array()
        => Assert.ThrowsAsync<InvalidOperationException>(() => base.Contains_over_field_string_array());

    // AnyTagEqualTo not (currently) supported on SQLite
    [Obsolete("Legacy filter support")]
    public override Task Legacy_AnyTagEqualTo()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Legacy_AnyTagEqualTo());

}
