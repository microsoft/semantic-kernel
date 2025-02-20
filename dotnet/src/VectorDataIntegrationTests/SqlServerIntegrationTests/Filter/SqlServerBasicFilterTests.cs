// Copyright (c) Microsoft. All rights reserved.

using SqlServerIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using Xunit;
using Xunit.Sdk;

namespace SqlServerIntegrationTests.Filter;

public class SqlServerBasicFilterTests(SqlServerBasicFilterTests.Fixture fixture)
    : BasicFilterTests<int>(fixture), IClassFixture<SqlServerBasicFilterTests.Fixture>
{
    // SQL Server doesn't support the null semantics that the default implementation relies on
    // "SELECT * FROM MyTable WHERE BooleanColumn = 1;" is fine
    // "SELECT * FROM MyTable WHERE BooleanColumn;" is not
    // TODO adsitnik: get it to work anyway
    public override Task Bool() => this.TestFilterAsync(r => r.Bool == true);

    // Same as above, "WHERE NOT BooleanColumn" is not supported
    public override Task Not_over_bool() => this.TestFilterAsync(r => r.Bool == false);

    public override async Task Not_over_Or()
    {
        // Test sends: WHERE (NOT (("Int" = 8) OR ("String" = 'foo')))
        // There's a NULL string in the database, and relational null semantics in conjunction with negation makes the default implementation fail.
        await Assert.ThrowsAsync<EqualException>(() => base.Not_over_Or());

        // Compensate by adding a null check:
        await this.TestFilterAsync(r => r.String != null && !(r.Int == 8 || r.String == "foo"));
    }

    public override async Task NotEqual_with_string()
    {
        // As above, null semantics + negation
        await Assert.ThrowsAsync<EqualException>(() => base.NotEqual_with_string());

        await this.TestFilterAsync(r => r.String != null && r.String != "foo");
    }

    public override Task Contains_over_field_string_array()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Contains_over_field_string_array());

    public override Task Contains_over_field_string_List()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Contains_over_field_string_List());

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
        public override TestStore TestStore => SqlServerTestStore.Instance;
    }
}
