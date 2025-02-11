// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Filter;
using Xunit;
using Xunit.Sdk;

namespace RedisIntegrationTests.Filter;

public abstract class RedisBasicFilterTests(FilterFixtureBase<string> fixture) : BasicFilterTestsBase<string>(fixture)
{
    #region Equality with null

    public override Task Equal_with_null_reference_type()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Equal_with_null_reference_type());

    public override Task Equal_with_null_captured()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Equal_with_null_captured());

    public override Task NotEqual_with_null_reference_type()
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

public class RedisJsonCollectionBasicFilterTests(RedisJsonCollectionFilterFixture fixture) : RedisBasicFilterTests(fixture), IClassFixture<RedisJsonCollectionFilterFixture>;

public class RedisHashSetCollectionBasicFilterTests(RedisHashSetCollectionFilterFixture fixture) : RedisBasicFilterTests(fixture), IClassFixture<RedisHashSetCollectionFilterFixture>
{
    // Null values are not supported in Redis HashSet
    public override Task Equal_with_null_reference_type()
        => Assert.ThrowsAsync<ThrowsException>(() => base.Equal_with_null_reference_type());

    public override Task Equal_with_null_captured()
        => Assert.ThrowsAsync<ThrowsException>(() => base.Equal_with_null_captured());

    public override Task NotEqual_with_null_reference_type()
        => Assert.ThrowsAsync<ThrowsException>(() => base.NotEqual_with_null_reference_type());

    public override Task NotEqual_with_null_captured()
        => Assert.ThrowsAsync<ThrowsException>(() => base.NotEqual_with_null_captured());

    // Array fields not supported on Redis HashSet
    public override Task Contains_over_field_string_array()
        => Assert.ThrowsAsync<InvalidOperationException>(() => base.Contains_over_field_string_array());

    public override Task Contains_over_field_string_List()
        => Assert.ThrowsAsync<InvalidOperationException>(() => base.Contains_over_field_string_List());

    [Obsolete("Legacy filter support")]
    public override Task Legacy_AnyTagEqualTo_array()
        => Assert.ThrowsAsync<InvalidOperationException>(() => base.Legacy_AnyTagEqualTo_array());

    [Obsolete("Legacy filter support")]
    public override Task Legacy_AnyTagEqualTo_List()
        => Assert.ThrowsAsync<InvalidOperationException>(() => base.Legacy_AnyTagEqualTo_List());
}
