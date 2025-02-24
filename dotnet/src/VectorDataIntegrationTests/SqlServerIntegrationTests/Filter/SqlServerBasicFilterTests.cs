// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using SqlServerIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using Xunit;
using Xunit.Sdk;

namespace SqlServerIntegrationTests.Filter;

public class SqlServerBasicFilterTests(SqlServerBasicFilterTests.Fixture fixture)
    : BasicFilterTests<int>(fixture), IClassFixture<SqlServerBasicFilterTests.Fixture>
{
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
        => Assert.ThrowsAsync<InvalidOperationException>(() => base.Contains_over_field_string_array());

    public override Task Contains_over_field_string_List()
        => Assert.ThrowsAsync<InvalidOperationException>(() => base.Contains_over_field_string_List());

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

        protected override string CollectionName
#if NET // make sure different TFMs use different collection names (as they may run in parralel and cause trouble)
            => "FilterTests-core";
#else
            => "FilterTests-framework";
#endif

        // Override to remove the string collection properties, which aren't (currently) supported on SqlServer
        protected override VectorStoreRecordDefinition GetRecordDefinition()
            => new()
            {
                Properties = base.GetRecordDefinition().Properties.Where(p => p.PropertyType != typeof(string[]) && p.PropertyType != typeof(List<string>)).ToList()
            };
    }
}
