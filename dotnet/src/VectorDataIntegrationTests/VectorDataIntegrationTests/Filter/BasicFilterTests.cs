// Copyright (c) Microsoft. All rights reserved.

using System.Linq.Expressions;
using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests.Filter;

public abstract class BasicFilterTests<TKey>(BasicFilterTests<TKey>.Fixture fixture)
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
    public virtual Task NotEqual_with_null_reference_type()
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

    [ConditionalFact]
    public virtual Task Bool_And_Bool()
        => this.TestFilterAsync(r => r.Bool && r.Bool);

    [ConditionalFact]
    public virtual Task Bool_Or_Not_Bool()
        => this.TestFilterAsync(r => r.Bool || !r.Bool, expectAllResults: true);

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

    [ConditionalFact]
    public virtual Task Not_over_bool_And_Comparison()
        => this.TestFilterAsync(r => !r.Bool && r.Int != int.MaxValue);

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
        Expression<Func<FilterRecord, bool>> filter,
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
                Filter = filter,
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
        Expression<Func<FilterRecord, bool>> expectedFilter,
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
                OldFilter = legacyFilter,
                Top = fixture.TestData.Count
            });

        var actual = await results.Results.Select(r => r.Record).OrderBy(r => r.Key).ToListAsync();

        Assert.Equal(expected, actual, (e, a) =>
            e.Int == a.Int &&
            e.String == a.String &&
            e.Int2 == a.Int2);
    }

#pragma warning disable CS1819 // Properties should not return arrays
#pragma warning disable CA1819 // Properties should not return arrays
    public class FilterRecord
    {
        public TKey Key { get; set; } = default!;
        public ReadOnlyMemory<float>? Vector { get; set; }

        public int Int { get; set; }
        public string? String { get; set; }
        public bool Bool { get; set; }
        public int Int2 { get; set; }
        public string[] StringArray { get; set; } = null!;
        public List<string> StringList { get; set; } = null!;
    }
#pragma warning restore CA1819 // Properties should not return arrays
#pragma warning restore CS1819

    public abstract class Fixture : VectorStoreCollectionFixture<TKey, FilterRecord>
    {
        protected override string CollectionName => "FilterTests";

        protected override VectorStoreRecordDefinition GetRecordDefinition()
            => new()
            {
                Properties =
                [
                    new VectorStoreRecordKeyProperty(nameof(FilterRecord.Key), typeof(TKey)),
                    new VectorStoreRecordVectorProperty(nameof(FilterRecord.Vector), typeof(ReadOnlyMemory<float>?))
                    {
                        Dimensions = 3,
                        DistanceFunction = this.DistanceFunction,
                        IndexKind = this.IndexKind
                    },

                    new VectorStoreRecordDataProperty(nameof(FilterRecord.Int), typeof(int)) { IsFilterable = true },
                    new VectorStoreRecordDataProperty(nameof(FilterRecord.String), typeof(string)) { IsFilterable = true },
                    new VectorStoreRecordDataProperty(nameof(FilterRecord.Bool), typeof(bool)) { IsFilterable = true },
                    new VectorStoreRecordDataProperty(nameof(FilterRecord.Int2), typeof(int)) { IsFilterable = true },
                    new VectorStoreRecordDataProperty(nameof(FilterRecord.StringArray), typeof(string[])) { IsFilterable = true },
                    new VectorStoreRecordDataProperty(nameof(FilterRecord.StringList), typeof(List<string>)) { IsFilterable = true }
                ]
            };

        protected override List<FilterRecord> BuildTestData()
        {
            // All records have the same vector - this fixture is about testing criteria filtering only
            var vector = new ReadOnlyMemory<float>([1, 2, 3]);

            return
            [
                new()
                {
                    Key = this.GenerateNextKey<TKey>(),
                    Int = 8,
                    String = "foo",
                    Bool = true,
                    Int2 = 80,
                    StringArray = ["x", "y"],
                    StringList = ["x", "y"],
                    Vector = vector
                },
                new()
                {
                    Key = this.GenerateNextKey<TKey>(),
                    Int = 9,
                    String = "bar",
                    Bool = false,
                    Int2 = 90,
                    StringArray = ["a", "b"],
                    StringList = ["a", "b"],
                    Vector = vector
                },
                new()
                {
                    Key = this.GenerateNextKey<TKey>(),
                    Int = 9,
                    String = "foo",
                    Bool = true,
                    Int2 = 9,
                    StringArray = ["x"],
                    StringList = ["x"],
                    Vector = vector
                },
                new()
                {
                    Key = this.GenerateNextKey<TKey>(),
                    Int = 10,
                    String = null,
                    Bool = false,
                    Int2 = 100,
                    StringArray = ["x", "y", "z"],
                    StringList = ["x", "y", "z"],
                    Vector = vector
                },
                new()
                {
                    Key = this.GenerateNextKey<TKey>(),
                    Int = 11,
                    Bool = true,
                    String = """with some special"characters'and\stuff""",
                    Int2 = 101,
                    StringArray = ["y", "z"],
                    StringList = ["y", "z"],
                    Vector = vector
                }
            ];
        }

        // In some databases (Azure AI Search), the data shows up but the filtering index isn't yet updated,
        // so filtered searches show empty results. Add a filter to the seed data check below.
        protected override Task WaitForDataAsync()
            => this.TestStore.WaitForDataAsync(this.Collection, recordCount: this.TestData.Count, r => r.Int > 0);
    }
}
