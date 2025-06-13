// Copyright (c) Microsoft. All rights reserved.

using MongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests.Filter;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace MongoDB.ConformanceTests.Filter;

public class MongoBasicQueryTests(MongoBasicQueryTests.Fixture fixture)
    : BasicQueryTests<string>(fixture), IClassFixture<MongoBasicQueryTests.Fixture>
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

    public override Task Equal_int_property_with_null_nullable_int()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Equal_int_property_with_null_nullable_int());

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
        public override TestStore TestStore => MongoTestStore.Instance;
    }
}
