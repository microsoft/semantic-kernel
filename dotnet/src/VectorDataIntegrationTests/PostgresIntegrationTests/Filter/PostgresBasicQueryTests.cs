// Copyright (c) Microsoft. All rights reserved.

using PostgresIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using Xunit;
using Xunit.Sdk;

namespace PostgresIntegrationTests.Filter;

public class PostgresBasicQueryTests(PostgresBasicQueryTests.Fixture fixture)
    : BasicQueryTests<int>(fixture), IClassFixture<PostgresBasicQueryTests.Fixture>
{
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

    public new class Fixture : BasicQueryTests<int>.QueryFixture
    {
        public override TestStore TestStore => PostgresTestStore.Instance;
    }
}
