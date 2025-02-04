// Copyright (c) Microsoft. All rights reserved.

using System.Linq.Expressions;
using Microsoft.Extensions.VectorData;
using Xunit;
using VectorDataSpecificationTests.Xunit;

namespace VectorDataSpecificationTests.Filter;

public abstract class BasicFilterTestsBase<TKey>(FilterFixtureBase<TKey> fixture)
    where TKey : notnull
{
    #region Equality

    [ConditionalFact]
    public virtual Task Equal_with_int()
        => this.TestFilter(r => r.Int == 8);

    [ConditionalFact]
    public virtual Task Equal_with_string()
        => this.TestFilter(r => r.String == "foo");

    [ConditionalFact]
    public virtual Task Equal_with_string_containing_special_characters()
        => this.TestFilter(r => r.String == """with some special"characters'and\stuff""");

    [ConditionalFact]
    public virtual Task Equal_with_string_is_not_Contains()
        => this.TestFilter(r => r.String == "some", expectZeroResults: true);

    [ConditionalFact]
    public virtual Task Equal_reversed()
        => this.TestFilter(r => 8 == r.Int);

    [ConditionalFact]
    public virtual Task Equal_with_null_reference_type()
        => this.TestFilter(r => r.String == null);

    [ConditionalFact]
    public virtual Task Equal_with_null_captured()
    {
        string? s = null;

        return this.TestFilter(r => r.String == s);
    }

    [ConditionalFact]
    public virtual Task NotEqual_with_int()
        => this.TestFilter(r => r.Int != 8);

    [ConditionalFact]
    public virtual Task NotEqual_with_string()
        => this.TestFilter(r => r.String != "foo");

    [ConditionalFact]
    public virtual Task NotEqual_reversed()
        => this.TestFilter(r => r.Int != 8);

    [ConditionalFact]
    public virtual Task NotEqual_with_null_referenceType()
        => this.TestFilter(r => r.String != null);

    [ConditionalFact]
    public virtual Task NotEqual_with_null_captured()
    {
        string? s = null;

        return this.TestFilter(r => r.String != s);
    }

    #endregion Equality

    #region Comparison

    [ConditionalFact]
    public virtual Task GreaterThan_with_int()
        => this.TestFilter(r => r.Int > 9);

    [ConditionalFact]
    public virtual Task GreaterThanOrEqual_with_int()
        => this.TestFilter(r => r.Int >= 9);

    [ConditionalFact]
    public virtual Task LessThan_with_int()
        => this.TestFilter(r => r.Int < 10);

    [ConditionalFact]
    public virtual Task LessThanOrEqual_with_int()
        => this.TestFilter(r => r.Int <= 10);

    #endregion Comparison

    #region Logical operators

    [ConditionalFact]
    public virtual Task And()
        => this.TestFilter(r => r.Int == 8 && r.String == "foo");

    [ConditionalFact]
    public virtual Task Or()
        => this.TestFilter(r => r.Int == 8 || r.String == "foo");

    [ConditionalFact]
    public virtual Task And_within_And()
        => this.TestFilter(r => (r.Int == 8 && r.String == "foo") && r.Int2 == 80);

    [ConditionalFact]
    public virtual Task And_within_Or()
        => this.TestFilter(r => (r.Int == 8 && r.String == "foo") || r.Int2 == 100);

    [ConditionalFact]
    public virtual Task Or_within_And()
        => this.TestFilter(r => (r.Int == 8 || r.Int == 9) && r.String == "foo");

    [ConditionalFact]
    public virtual Task Not_over_Equal()
        // ReSharper disable once NegativeEqualityExpression
        => this.TestFilter(r => !(r.Int == 8));

    [ConditionalFact]
    public virtual Task Not_over_NotEqual()
        // ReSharper disable once NegativeEqualityExpression
        => this.TestFilter(r => !(r.Int != 8));

    [ConditionalFact]
    public virtual Task Not_over_And()
        => this.TestFilter(r => !(r.Int == 8 && r.String == "foo"));

    [ConditionalFact]
    public virtual Task Not_over_Or()
        => this.TestFilter(r => !(r.Int == 8 || r.String == "foo"));

    #endregion Logical operators

    #region Contains

    [ConditionalFact]
    public virtual Task Contains_over_field_string_array()
        => this.TestFilter(r => r.Strings.Contains("x"));

    [ConditionalFact]
    public virtual Task Contains_over_inline_int_array()
        => this.TestFilter(r => new[] { 8, 10 }.Contains(r.Int));

    [ConditionalFact]
    public virtual Task Contains_over_inline_string_array()
        => this.TestFilter(r => new[] { "foo", "baz", "unknown" }.Contains(r.String));

    [ConditionalFact]
    public virtual Task Contains_over_inline_string_array_with_weird_chars()
        => this.TestFilter(r => new[] { "foo", "baz", "un  , ' \"" }.Contains(r.String));

    [ConditionalFact]
    public virtual Task Contains_over_captured_string_array()
    {
        var array = new[] { "foo", "baz", "unknown" };

        return this.TestFilter(r => array.Contains(r.String));
    }

    #endregion Contains

    [ConditionalFact]
    public virtual Task Captured_variable()
    {
        // ReSharper disable once ConvertToConstant.Local
        var i = 8;

        return this.TestFilter(r => r.Int == i);
    }

    #region Legacy filter support

    [Fact]
    [Obsolete("Legacy filter support")]
    public virtual Task Legacy_equality()
        => this.TestLegacyFilter(
            new VectorSearchFilter().EqualTo("Int", 8),
            r => r.Int == 8);

    [Fact]
    [Obsolete("Legacy filter support")]
    public virtual Task Legacy_And()
        => this.TestLegacyFilter(
            new VectorSearchFilter().EqualTo("Int", 8).EqualTo("String", "foo"),
            r => r.Int == 8);

    [Fact]
    [Obsolete("Legacy filter support")]
    public virtual Task Legacy_AnyTagEqualTo()
        => this.TestLegacyFilter(
            new VectorSearchFilter().AnyTagEqualTo("Strings", "x"),
            r => r.Strings.Contains("x"));

    #endregion Legacy filter support

    protected virtual async Task TestFilter(
        Expression<Func<FilterRecord<TKey>, bool>> filter,
        bool expectZeroResults = false,
        bool expectAllResults = false)
    {
        var expected = fixture.TestData.AsQueryable().Where(filter).OrderBy(r => r.Key).ToList();

        if (expected.Count == 0 && !expectZeroResults)
        {
            Assert.Fail("The test returns zero results, and so is unreliable");
        }

        if (expected.Count == fixture.TestData.Count && !expectAllResults)
        {
            Assert.Fail("The test returns all results, and so is unreliable");
        }

        var results = await fixture.Collection.VectorizedSearchAsync(
            new ReadOnlyMemory<float>([1, 2, 3]),
            new()
            {
                NewFilter = filter,
                Top = 1000
            });

        var actual = await results.Results.Select(r => r.Record).OrderBy(r => r.Key).ToListAsync();

        Assert.Equal(expected, actual, (e, a) =>
            e.Int == a.Int &&
            e.String == a.String &&
            e.Int2 == a.Int2);
    }

    [Obsolete("Legacy filter support")]
    protected virtual async Task TestLegacyFilter(
        VectorSearchFilter legacyFilter,
        Expression<Func<FilterRecord<TKey>, bool>> expectedFilter,
        bool expectZeroResults = false,
        bool expectAllResults = false)
    {
        var expected = fixture.TestData.AsQueryable().Where(expectedFilter).OrderBy(r => r.Key).ToList();

        if (expected.Count == 0 && !expectZeroResults)
        {
            Assert.Fail("The test returns zero results, and so is unreliable");
        }

        if (expected.Count == fixture.TestData.Count && !expectAllResults)
        {
            Assert.Fail("The test returns all results, and so is unreliable");
        }

        var results = await fixture.Collection.VectorizedSearchAsync(
            new ReadOnlyMemory<float>([1, 2, 3]),
            new()
            {
                Filter = legacyFilter,
                Top = 1000
            });

        var actual = await results.Results.Select(r => r.Record).OrderBy(r => r.Key).ToListAsync();

        Assert.Equal(expected, actual, (e, a) =>
            e.Int == a.Int &&
            e.String == a.String &&
            e.Int2 == a.Int2);
    }
}
