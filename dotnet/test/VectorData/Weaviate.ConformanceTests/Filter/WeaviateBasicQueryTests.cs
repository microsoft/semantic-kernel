// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests.Filter;
using VectorData.ConformanceTests.Support;
using Weaviate.ConformanceTests.Support;
using Xunit;

namespace Weaviate.ConformanceTests.Filter;

public class WeaviateBasicQueryTests(WeaviateBasicQueryTests.Fixture fixture)
    : BasicQueryTests<Guid>(fixture), IClassFixture<WeaviateBasicQueryTests.Fixture>
{
    #region Filter by null

    // Null-state indexing needs to be set up, but that's not supported yet (#10358).
    // We could interact with Weaviate directly (not via the abstraction) to do this.

    public override Task Equal_with_null_reference_type()
        => Assert.ThrowsAsync<VectorStoreException>(() => base.Equal_with_null_reference_type());

    public override Task Equal_with_null_captured()
        => Assert.ThrowsAsync<VectorStoreException>(() => base.Equal_with_null_captured());

    public override Task NotEqual_with_null_captured()
        => Assert.ThrowsAsync<VectorStoreException>(() => base.NotEqual_with_null_captured());

    public override Task NotEqual_with_null_reference_type()
        => Assert.ThrowsAsync<VectorStoreException>(() => base.NotEqual_with_null_reference_type());

    public override Task Equal_int_property_with_null_nullable_int()
        => Assert.ThrowsAsync<VectorStoreException>(() => base.Equal_int_property_with_null_nullable_int());

    #endregion

    #region Not

    // Weaviate currently doesn't support NOT (https://github.com/weaviate/weaviate/issues/3683)
    public override Task Not_over_And()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Not_over_And());

    public override Task Not_over_Or()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Not_over_Or());

    #endregion

    #region Unsupported Contains scenarios

    public override Task Contains_over_captured_string_array()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Contains_over_captured_string_array());

    public override Task Contains_over_inline_int_array()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Contains_over_inline_int_array());

    public override Task Contains_over_inline_string_array()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Contains_over_inline_int_array());

    public override Task Contains_over_inline_string_array_with_weird_chars()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Contains_over_inline_string_array_with_weird_chars());

    #endregion

    public new class Fixture : BasicQueryTests<Guid>.QueryFixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;
    }
}
