// Copyright (c) Microsoft. All rights reserved.

using CosmosMongoDBIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace CosmosMongoDBIntegrationTests.Filter;

public class CosmosMongoBasicFilterTests(CosmosMongoBasicFilterTests.Fixture fixture)
    : BasicFilterTests<string>(fixture), IClassFixture<CosmosMongoBasicFilterTests.Fixture>
{
    // Specialized MongoDB syntax for NOT over Contains ($nin)
    [ConditionalFact]
    public virtual Task Not_over_Contains()
        => this.TestFilterAsync(
            r => !new[] { 8, 10 }.Contains(r.Int),
            r => !new[] { 8, 10 }.Contains((int)r["Int"]!));

    #region Null checking

    // MongoDB currently doesn't support null checking ({ "Foo" : null }) in vector search pre-filters
    public override Task Equal_with_null_reference_type()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Equal_with_null_reference_type());

    public override Task Equal_with_null_captured()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Equal_with_null_captured());

    public override Task NotEqual_with_null_reference_type()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.NotEqual_with_null_reference_type());

    public override Task NotEqual_with_null_captured()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.NotEqual_with_null_captured());

    #endregion

    #region Not

    // MongoDB currently doesn't support NOT in vector search pre-filters
    // (https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-stage/#atlas-vector-search-pre-filter)
    public override Task Not_over_And()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Not_over_And());

    public override Task Not_over_Or()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Not_over_Or());

    #endregion

    public override Task Contains_over_field_string_array()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Contains_over_field_string_array());

    public override Task Contains_over_field_string_List()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Contains_over_field_string_List());

    // AnyTagEqualTo not (currently) supported on SQLite
    [Obsolete("Legacy filter support")]
    public override Task Legacy_AnyTagEqualTo_array()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Legacy_AnyTagEqualTo_array());

    [Obsolete("Legacy filter support")]
    public override Task Legacy_AnyTagEqualTo_List()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Legacy_AnyTagEqualTo_List());

    public new class Fixture : BasicFilterTests<string>.Fixture
    {
        public override TestStore TestStore => CosmosMongoDBTestStore.Instance;

        protected override string IndexKind => Microsoft.Extensions.VectorData.IndexKind.IvfFlat;
        protected override string DistanceFunction => Microsoft.Extensions.VectorData.DistanceFunction.CosineDistance;
    }
}
