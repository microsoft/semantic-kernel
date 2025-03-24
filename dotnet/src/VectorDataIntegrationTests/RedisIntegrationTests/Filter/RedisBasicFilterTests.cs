﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Redis;
using RedisIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using Xunit;
using Xunit.Sdk;

namespace RedisIntegrationTests.Filter;

public abstract class RedisBasicFilterTests(BasicFilterTests<string>.Fixture fixture)
    : BasicFilterTests<string>(fixture)
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

    public override Task Bool_And_Bool()
        => Assert.ThrowsAsync<InvalidOperationException>(() => base.Bool_And_Bool());

    public override Task Bool_Or_Not_Bool()
        => Assert.ThrowsAsync<InvalidOperationException>(() => base.Bool_Or_Not_Bool());

    public override Task Not_over_bool_And_Comparison()
        => Assert.ThrowsAsync<InvalidOperationException>(() => base.Not_over_bool_And_Comparison());

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

public class RedisJsonCollectionBasicFilterTests(RedisJsonCollectionBasicFilterTests.Fixture fixture)
    : RedisBasicFilterTests(fixture), IClassFixture<RedisJsonCollectionBasicFilterTests.Fixture>
{
    public new class Fixture : BasicFilterTests<string>.Fixture
    {
        public override TestStore TestStore => RedisTestStore.JsonInstance;

        protected override string CollectionName => "JsonCollectionFilterTests";

        // Override to remove the bool property, which isn't (currently) supported on Redis/JSON
        protected override VectorStoreRecordDefinition GetRecordDefinition()
            => new()
            {
                Properties = base.GetRecordDefinition().Properties.Where(p => p.PropertyType != typeof(bool)).ToList()
            };

        protected override IVectorStoreRecordCollection<string, FilterRecord> CreateCollection()
            => new RedisJsonVectorStoreRecordCollection<FilterRecord>(
                RedisTestStore.JsonInstance.Database,
                this.CollectionName,
                new() { VectorStoreRecordDefinition = this.GetRecordDefinition() });
    }
}

public class RedisHashSetCollectionBasicFilterTests(RedisHashSetCollectionBasicFilterTests.Fixture fixture)
    : RedisBasicFilterTests(fixture), IClassFixture<RedisHashSetCollectionBasicFilterTests.Fixture>
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

    public new class Fixture : BasicFilterTests<string>.Fixture
    {
        public override TestStore TestStore => RedisTestStore.HashSetInstance;

        protected override string CollectionName => "HashSetCollectionFilterTests";

        // Override to remove the bool property, which isn't (currently) supported on Redis
        protected override VectorStoreRecordDefinition GetRecordDefinition()
            => new()
            {
                Properties = base.GetRecordDefinition().Properties.Where(p =>
                    p.PropertyType != typeof(bool) &&
                    p.PropertyType != typeof(string[]) &&
                    p.PropertyType != typeof(List<string>)).ToList()
            };

        protected override IVectorStoreRecordCollection<string, FilterRecord> CreateCollection()
            => new RedisHashSetVectorStoreRecordCollection<FilterRecord>(
                RedisTestStore.HashSetInstance.Database,
                this.CollectionName,
                new() { VectorStoreRecordDefinition = this.GetRecordDefinition() });

        protected override List<FilterRecord> BuildTestData()
        {
            var testData = base.BuildTestData();

            foreach (var record in testData)
            {
                // Null values are not supported in Redis hashsets
                record.String ??= string.Empty;
            }

            return testData;
        }
    }
}
