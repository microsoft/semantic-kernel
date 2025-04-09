// Copyright (c) Microsoft. All rights reserved.

using MongoDBIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace MongoDBIntegrationTests.Filter;

public class MongoDBBasicQueryTests(MongoDBBasicQueryTests.Fixture fixture)
    : BasicQueryTests<string>(fixture), IClassFixture<MongoDBBasicQueryTests.Fixture>
{
    // Specialized MongoDB syntax for NOT over Contains ($nin)
    [ConditionalFact]
    public virtual Task Not_over_Contains()
        => this.TestFilterAsync(
            r => !new[] { 8, 10 }.Contains(r.Int),
            r => !new[] { 8, 10 }.Contains((int)r["Int"]!));

    // MongoDB currently doesn't support null checking ({ "Foo" : null }) in vector search pre-filters
    public override Task Equal_with_null_reference_type()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Equal_with_null_reference_type());

    public override Task Equal_with_null_captured()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Equal_with_null_captured());

    public override Task NotEqual_with_null_reference_type()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.NotEqual_with_null_reference_type());

    public override Task NotEqual_with_null_captured()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.NotEqual_with_null_captured());

    // MongoDB currently doesn't support NOT in vector search pre-filters
    // (https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-stage/#atlas-vector-search-pre-filter)
    public override Task Not_over_And()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Not_over_And());

    public override Task Not_over_Or()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Not_over_Or());

    public override Task Contains_over_field_string_array()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Contains_over_field_string_array());

    public override Task Contains_over_field_string_List()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Contains_over_field_string_List());

    public new class Fixture : BasicQueryTests<string>.QueryFixture
    {
        public override TestStore TestStore => MongoDBTestStore.Instance;
    }
}
