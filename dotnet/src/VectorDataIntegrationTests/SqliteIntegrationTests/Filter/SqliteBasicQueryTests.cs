// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using SqliteIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using Xunit;
using Xunit.Sdk;

namespace SqliteIntegrationTests.Filter;

#pragma warning disable CS0252 // Possible unintended reference comparison; left hand side needs cast

public class SqliteBasicQueryTests(SqliteBasicQueryTests.Fixture fixture)
    : BasicQueryTests<ulong>(fixture), IClassFixture<SqliteBasicQueryTests.Fixture>
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

    // Array fields not (currently) supported on SQLite (see #10343)
    public override Task Contains_over_field_string_array()
        => Assert.ThrowsAsync<InvalidOperationException>(() => base.Contains_over_field_string_array());

    // List fields not (currently) supported on SQLite (see #10343)
    public override Task Contains_over_field_string_List()
        => Assert.ThrowsAsync<InvalidOperationException>(() => base.Contains_over_field_string_List());

    public new class Fixture : BasicQueryTests<ulong>.QueryFixture
    {
        public override TestStore TestStore => SqliteTestStore.Instance;

        // Override to remove the string array property, which isn't (currently) supported on SQLite
        public override VectorStoreRecordDefinition GetRecordDefinition()
            => new()
            {
                Properties = base.GetRecordDefinition().Properties.Where(p => p.PropertyType != typeof(string[]) && p.PropertyType != typeof(List<string>)).ToList()
            };
    }
}
