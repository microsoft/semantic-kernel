// Copyright (c) Microsoft. All rights reserved.

using System.Linq.Expressions;
using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests.Filter;

public abstract class BasicFilterTestsBase<TKey>(FilterFixtureBase<TKey> fixture)
    where TKey : notnull
{
    #region Equality

    [ConditionalFact]
    public virtual Task Equal_with_int()
        => this.TestFilterAsync(r => r.Int == 8);

    [ConditionalFact]
    public virtual Task Equal_with_string()
        => this.TestFilterAsync(r => r.String == "foo");

    [ConditionalFact]
    public virtual Task Equal_with_string_containing_special_characters()
        => this.TestFilterAsync(r => r.String == """with some special"characters'and\stuff""");

    [ConditionalFact]
    public virtual Task Equal_with_string_is_not_Contains()
        => this.TestFilterAsync(r => r.String == "some", expectZeroResults: true);

    [ConditionalFact]
    public virtual Task Equal_reversed()
        => this.TestFilterAsync(r => 8 == r.Int);

    [ConditionalFact]
    public virtual Task Equal_with_null_reference_type()
        => this.TestFilterAsync(r => r.String == null);

    [ConditionalFact]
    public virtual Task Equal_with_null_captured()
    {
        string? s = null;

        return this.TestFilterAsync(r => r.String == s);
    }

    [ConditionalFact]
    public virtual Task NotEqual_with_int()
        => this.TestFilterAsync(r => r.Int != 8);

    [ConditionalFact]
    public virtual Task NotEqual_with_string()
        => this.TestFilterAsync(r => r.String != "foo");

    [ConditionalFact]
    public virtual Task NotEqual_reversed()
        => this.TestFilterAsync(r => r.Int != 8);

    [ConditionalFact]
    public virtual Task NotEqual_with_null_referenceType()
        => this.TestFilterAsync(r => r.String != null);

    [ConditionalFact]
    public virtual Task NotEqual_with_null_captured()
    {
        string? s = null;

        return this.TestFilterAsync(r => r.String != s);
    }

    [ConditionalFact]
    public virtual Task Bool()
        => this.TestFilterAsync(r => r.Bool);

    #endregion Equality

    #region Comparison

    [ConditionalFact]
    public virtual Task GreaterThan_with_int()
        => this.TestFilterAsync(r => r.Int > 9);

    [ConditionalFact]
    public virtual Task GreaterThanOrEqual_with_int()
        => this.TestFilterAsync(r => r.Int >= 9);

    [ConditionalFact]
    public virtual Task LessThan_with_int()
        => this.TestFilterAsync(r => r.Int < 10);

    [ConditionalFact]
    public virtual Task LessThanOrEqual_with_int()
        => this.TestFilterAsync(r => r.Int <= 10);

    #endregion Comparison

    #region Logical operators

    [ConditionalFact]
    public virtual Task And()
        => this.TestFilterAsync(r => r.Int == 8 && r.String == "foo");

    [ConditionalFact]
    public virtual Task Or()
        => this.TestFilterAsync(r => r.Int == 8 || r.String == "foo");

    [ConditionalFact]
    public virtual Task And_within_And()
        => this.TestFilterAsync(r => (r.Int == 8 && r.String == "foo") && r.Int2 == 80);

    [ConditionalFact]
    public virtual Task And_within_Or()
        => this.TestFilterAsync(r => (r.Int == 8 && r.String == "foo") || r.Int2 == 100);

    [ConditionalFact]
    public virtual Task Or_within_And()
        => this.TestFilterAsync(r => (r.Int == 8 || r.Int == 9) && r.String == "foo");

    [ConditionalFact]
    public virtual Task Not_over_Equal()
        // ReSharper disable once NegativeEqualityExpression
        => this.TestFilterAsync(r => !(r.Int == 8));

    [ConditionalFact]
    public virtual Task Not_over_NotEqual()
        // ReSharper disable once NegativeEqualityExpression
        => this.TestFilterAsync(r => !(r.Int != 8));

    [ConditionalFact]
    public virtual Task Not_over_And()
        => this.TestFilterAsync(r => !(r.Int == 8 && r.String == "foo"));

    [ConditionalFact]
    public virtual Task Not_over_Or()
        => this.TestFilterAsync(r => !(r.Int == 8 || r.String == "foo"));

    [ConditionalFact]
    public virtual Task Not_over_bool()
        => this.TestFilterAsync(r => !r.Bool);

    #endregion Logical operators

    #region Contains

    [ConditionalFact]
    public virtual Task Contains_over_field_string_array()
        => this.TestFilterAsync(r => r.StringArray.Contains("x"));

    [ConditionalFact]
    public virtual Task Contains_over_field_string_List()
        => this.TestFilterAsync(r => r.StringList.Contains("x"));

    [ConditionalFact]
    public virtual Task Contains_over_inline_int_array()
        => this.TestFilterAsync(r => new[] { 8, 10 }.Contains(r.Int));

    [ConditionalFact]
    public virtual Task Contains_over_inline_string_array()
        => this.TestFilterAsync(r => new[] { "foo", "baz", "unknown" }.Contains(r.String));

    [ConditionalFact]
    public virtual Task Contains_over_inline_string_array_with_weird_chars()
        => this.TestFilterAsync(r => new[] { "foo", "baz", "un  , ' \"" }.Contains(r.String));

    [ConditionalFact]
    public virtual Task Contains_over_captured_string_array()
    {
        var array = new[] { "foo", "baz", "unknown" };

        return this.TestFilterAsync(r => array.Contains(r.String));
    }

    #endregion Contains

    [ConditionalFact]
    public virtual Task Captured_variable()
    {
        // ReSharper disable once ConvertToConstant.Local
        var i = 8;

        return this.TestFilterAsync(r => r.Int == i);
    }

    #region Legacy filter support

    [ConditionalFact]
    [Obsolete("Legacy filter support")]
    public virtual Task Legacy_equality()
        => this.TestLegacyFilterAsync(
            new VectorSearchFilter().EqualTo("Int", 8),
            r => r.Int == 8);

    [ConditionalFact]
    [Obsolete("Legacy filter support")]
    public virtual Task Legacy_And()
        => this.TestLegacyFilterAsync(
            new VectorSearchFilter().EqualTo("Int", 8).EqualTo("String", "foo"),
            r => r.Int == 8);

    [ConditionalFact]
    [Obsolete("Legacy filter support")]
    public virtual Task Legacy_AnyTagEqualTo_array()
        => this.TestLegacyFilterAsync(
            new VectorSearchFilter().AnyTagEqualTo("StringArray", "x"),
            r => r.StringArray.Contains("x"));

    [ConditionalFact]
    [Obsolete("Legacy filter support")]
    public virtual Task Legacy_AnyTagEqualTo_List()
        => this.TestLegacyFilterAsync(
            new VectorSearchFilter().AnyTagEqualTo("StringList", "x"),
            r => r.StringArray.Contains("x"));

    #endregion Legacy filter support

    protected virtual async Task TestFilterAsync(
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
                Top = fixture.TestData.Count
            });

        var actual = await results.Results.Select(r => r.Record).OrderBy(r => r.Key).ToListAsync();

        Assert.Equal(expected, actual, (e, a) =>
            e.Int == a.Int &&
            e.String == a.String &&
            e.Int2 == a.Int2);
    }

    [Obsolete("Legacy filter support")]
    protected virtual async Task TestLegacyFilterAsync(
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
                Top = fixture.TestData.Count
            });

        var actual = await results.Results.Select(r => r.Record).OrderBy(r => r.Key).ToListAsync();

        Assert.Equal(expected, actual, (e, a) =>
            e.Int == a.Int &&
            e.String == a.String &&
            e.Int2 == a.Int2);
    }
}
