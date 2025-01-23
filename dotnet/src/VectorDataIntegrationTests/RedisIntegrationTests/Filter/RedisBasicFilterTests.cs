// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Filter;
using Xunit;

namespace RedisIntegrationTests.Filter;

public class RedisBasicFilterTests(RedisFilterFixture fixture) : BasicFilterTestsBase<string>(fixture), IClassFixture<RedisFilterFixture>
{
    #region Equality with null

    public override Task Equal_with_null_reference_type()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Equal_with_null_reference_type());

    public override Task Equal_with_null_captured()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Equal_with_null_captured());

    public override Task NotEqual_with_null_referenceType()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Equal_with_null_reference_type());

    public override Task NotEqual_with_null_captured()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.NotEqual_with_null_captured());

    #endregion

    #region Bool

    public override Task Bool()
        => Assert.ThrowsAsync<InvalidOperationException>(() => base.Bool());

    public override Task Not_over_bool()
        => Assert.ThrowsAsync<InvalidOperationException>(() => base.Not_over_bool());

    #endregion

    #region Contains

    public override Task Contains_over_inline_int_array()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Contains_over_inline_int_array());

    public override Task Contains_over_inline_string_array()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Contains_over_inline_string_array());

    public override Task Contains_over_inline_string_array_with_weird_chars()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Contains_over_inline_string_array_with_weird_chars());

    public override Task Contains_over_captured_string_array()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Contains_over_captured_string_array());

    #endregion
}
