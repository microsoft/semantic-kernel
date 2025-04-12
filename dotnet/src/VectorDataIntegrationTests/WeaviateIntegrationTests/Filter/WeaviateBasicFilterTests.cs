// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using WeaviateIntegrationTests.Support;
using Xunit;
using Xunit.Sdk;

namespace WeaviateIntegrationTests.Filter;

public class WeaviateBasicFilterTests(WeaviateBasicFilterTests.Fixture fixture)
    : BasicFilterTests<Guid>(fixture), IClassFixture<WeaviateBasicFilterTests.Fixture>
{
    #region Filter by null

    // Null-state indexing needs to be set up, but that's not supported yet (#10358).
    // We could interact with Weaviate directly (not via the abstraction) to do this.

    public override Task Equal_with_null_reference_type()
        => Assert.ThrowsAsync<VectorStoreOperationException>(() => base.Equal_with_null_reference_type());

    public override Task Equal_with_null_captured()
        => Assert.ThrowsAsync<VectorStoreOperationException>(() => base.Equal_with_null_captured());

    public override Task NotEqual_with_null_captured()
        => Assert.ThrowsAsync<VectorStoreOperationException>(() => base.NotEqual_with_null_captured());

    public override Task NotEqual_with_null_reference_type()
        => Assert.ThrowsAsync<VectorStoreOperationException>(() => base.NotEqual_with_null_reference_type());

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

    // In Weaviate, string equality on multi-word textual properties depends on tokenization
    // (https://weaviate.io/developers/weaviate/api/graphql/filters#multi-word-queries-in-equal-filters)
    public override Task Equal_with_string_is_not_Contains()
        => Assert.ThrowsAsync<FailException>(() => base.Equal_with_string_is_not_Contains());

    public new class Fixture : BasicFilterTests<Guid>.Fixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;
    }
}
