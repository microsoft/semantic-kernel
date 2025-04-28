// Copyright (c) Microsoft. All rights reserved.

using System.Linq.Expressions;
using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

#pragma warning disable CS8605 // Unboxing a possibly null value.
#pragma warning disable CS0252 // Possible unintended reference comparison; left hand side needs cast
#pragma warning disable RCS1098 // Constant values should be placed on right side of comparisons

namespace VectorDataSpecificationTests.Filter;

public abstract class BasicFilterTests<TKey>(BasicFilterTests<TKey>.Fixture fixture)
    where TKey : notnull
{
    #region Equality

    [ConditionalFact]
    public virtual Task Equal_with_int()
        => this.TestFilterAsync(
            r => r.Int == 8,
            r => (int)r["Int"] == 8);

    [ConditionalFact]
    public virtual Task Equal_with_string()
        => this.TestFilterAsync(
            r => r.String == "foo",
            r => r["String"] == "foo");

    [ConditionalFact]
    public virtual Task Equal_with_string_containing_special_characters()
        => this.TestFilterAsync(
            r => r.String == """with some special"characters'and\stuff""",
            r => r["String"] == """with some special"characters'and\stuff""");

    [ConditionalFact]
    public virtual Task Equal_with_string_is_not_Contains()
        => this.TestFilterAsync(
            r => r.String == "some",
            r => r["String"] == "some",
            expectZeroResults: true);

    [ConditionalFact]
    public virtual Task Equal_reversed()
        => this.TestFilterAsync(
            r => 8 == r.Int,
            r => 8 == (int)r["Int"]);

    [ConditionalFact]
    public virtual Task Equal_with_null_reference_type()
        => this.TestFilterAsync(
            r => r.String == null,
            r => r["String"] == null);

    [ConditionalFact]
    public virtual Task Equal_with_null_captured()
    {
        string? s = null;

        return this.TestFilterAsync(
            r => r.String == s,
            r => r["String"] == s);
    }

    [ConditionalFact]
    public virtual Task NotEqual_with_int()
        => this.TestFilterAsync(
            r => r.Int != 8,
            r => (int)r["Int"] != 8);

    [ConditionalFact]
    public virtual Task NotEqual_with_string()
        => this.TestFilterAsync(
            r => r.String != "foo",
            r => r["String"] != "foo");

    [ConditionalFact]
    public virtual Task NotEqual_reversed()
        => this.TestFilterAsync(
            r => r.Int != 8,
            r => (int)r["Int"] != 8);

    [ConditionalFact]
    public virtual Task NotEqual_with_null_reference_type()
        => this.TestFilterAsync(
            r => r.String != null,
            r => r["String"] != null);

    [ConditionalFact]
    public virtual Task NotEqual_with_null_captured()
    {
        string? s = null;

        return this.TestFilterAsync(
            r => r.String != s,
            r => r["String"] != s);
    }

    [ConditionalFact]
    public virtual Task Bool()
        => this.TestFilterAsync(
            r => r.Bool,
            r => (bool)r["Bool"]);

    [ConditionalFact]
    public virtual Task Bool_And_Bool()
        => this.TestFilterAsync(
            r => r.Bool && r.Bool,
            r => (bool)r["Bool"] && (bool)r["Bool"]);

    [ConditionalFact]
    public virtual Task Bool_Or_Not_Bool()
        => this.TestFilterAsync(
            r => r.Bool || !r.Bool,
            r => (bool)r["Bool"] || !(bool)r["Bool"],
            expectAllResults: true);

    #endregion Equality

    #region Comparison

    [ConditionalFact]
    public virtual Task GreaterThan_with_int()
        => this.TestFilterAsync(
            r => r.Int > 9,
            r => (int)r["Int"] > 9);

    [ConditionalFact]
    public virtual Task GreaterThanOrEqual_with_int()
        => this.TestFilterAsync(
            r => r.Int >= 9,
            r => (int)r["Int"] >= 9);

    [ConditionalFact]
    public virtual Task LessThan_with_int()
        => this.TestFilterAsync(
            r => r.Int < 10,
            r => (int)r["Int"] < 10);

    [ConditionalFact]
    public virtual Task LessThanOrEqual_with_int()
        => this.TestFilterAsync(
            r => r.Int <= 10,
            r => (int)r["Int"] <= 10);

    #endregion Comparison

    #region Logical operators

    [ConditionalFact]
    public virtual Task And()
        => this.TestFilterAsync(
            r => r.Int == 8 && r.String == "foo",
            r => (int)r["Int"] == 8 && r["String"] == "foo");

    [ConditionalFact]
    public virtual Task Or()
        => this.TestFilterAsync(
            r => r.Int == 8 || r.String == "foo",
            r => (int)r["Int"] == 8 || r["String"] == "foo");

    [ConditionalFact]
    public virtual Task And_within_And()
        => this.TestFilterAsync(
            r => (r.Int == 8 && r.String == "foo") && r.Int2 == 80,
            r => ((int)r["Int"] == 8 && r["String"] == "foo") && (int)r["Int2"] == 80);

    [ConditionalFact]
    public virtual Task And_within_Or()
        => this.TestFilterAsync(
            r => (r.Int == 8 && r.String == "foo") || r.Int2 == 100,
            r => ((int)r["Int"] == 8 && r["String"] == "foo") || (int)r["Int2"] == 100);

    [ConditionalFact]
    public virtual Task Or_within_And()
        => this.TestFilterAsync(
            r => (r.Int == 8 || r.Int == 9) && r.String == "foo",
            r => ((int)r["Int"] == 8 || (int)r["Int"] == 9) && r["String"] == "foo");

    [ConditionalFact]
    public virtual Task Not_over_Equal()
        // ReSharper disable once NegativeEqualityExpression
        => this.TestFilterAsync(
            r => !(r.Int == 8),
            r => !((int)r["Int"] == 8));

    [ConditionalFact]
    public virtual Task Not_over_NotEqual()
        // ReSharper disable once NegativeEqualityExpression
        => this.TestFilterAsync(
            r => !(r.Int != 8),
            r => !((int)r["Int"] != 8));

    [ConditionalFact]
    public virtual Task Not_over_And()
        => this.TestFilterAsync(
            r => !(r.Int == 8 && r.String == "foo"),
            r => !((int)r["Int"] == 8 && r["String"] == "foo"));

    [ConditionalFact]
    public virtual Task Not_over_Or()
        => this.TestFilterAsync(
            r => !(r.Int == 8 || r.String == "foo"),
            r => !((int)r["Int"] == 8 || r["String"] == "foo"));

    [ConditionalFact]
    public virtual Task Not_over_bool()
        => this.TestFilterAsync(
            r => !r.Bool,
            r => !(bool)r["Bool"]);

    [ConditionalFact]
    public virtual Task Not_over_bool_And_Comparison()
        => this.TestFilterAsync(
            r => !r.Bool && r.Int != int.MaxValue,
            r => !(bool)r["Bool"] && (int)r["Int"] != int.MaxValue);

    #endregion Logical operators

    #region Contains

    [ConditionalFact]
    public virtual Task Contains_over_field_string_array()
        => this.TestFilterAsync(
            r => r.StringArray.Contains("x"),
            r => ((string[])r["StringArray"]!).Contains("x"));

    [ConditionalFact]
    public virtual Task Contains_over_field_string_List()
        => this.TestFilterAsync(
            r => r.StringList.Contains("x"),
            r => ((List<string>)r["StringList"]!).Contains("x"));

    [ConditionalFact]
    public virtual Task Contains_over_inline_int_array()
        => this.TestFilterAsync(
            r => new[] { 8, 10 }.Contains(r.Int),
            r => new[] { 8, 10 }.Contains((int)r["Int"]));

    [ConditionalFact]
    public virtual Task Contains_over_inline_string_array()
        => this.TestFilterAsync(
            r => new[] { "foo", "baz", "unknown" }.Contains(r.String),
            r => new[] { "foo", "baz", "unknown" }.Contains(r["String"]));

    [ConditionalFact]
    public virtual Task Contains_over_inline_string_array_with_weird_chars()
        => this.TestFilterAsync(
            r => new[] { "foo", "baz", "un  , ' \"" }.Contains(r.String),
            r => new[] { "foo", "baz", "un  , ' \"" }.Contains(r["String"]));

    [ConditionalFact]
    public virtual Task Contains_over_captured_string_array()
    {
        var array = new[] { "foo", "baz", "unknown" };

        return this.TestFilterAsync(
            r => array.Contains(r.String),
            r => array.Contains(r["String"]));
    }

    #endregion Contains

    [ConditionalFact]
    public virtual Task Captured_variable()
    {
        // ReSharper disable once ConvertToConstant.Local
        var i = 8;

        return this.TestFilterAsync(
            r => r.Int == i,
            r => (int)r["Int"] == i);
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

    protected virtual async Task<List<FilterRecord>> GetRecords(
        Expression<Func<FilterRecord, bool>> filter, int top, ReadOnlyMemory<float> vector)
        => await fixture.Collection.SearchEmbeddingAsync(
                vector,
                top: top,
                new() { Filter = filter })
            .Select(r => r.Record).OrderBy(r => r.Key).ToListAsync();

    protected virtual async Task<List<Dictionary<string, object?>>> GetDynamicRecords(
        Expression<Func<Dictionary<string, object?>, bool>> dynamicFilter, int top, ReadOnlyMemory<float> vector)
        => await fixture.DynamicCollection.SearchEmbeddingAsync(
                vector,
                top: top,
                new() { Filter = dynamicFilter })
            .Select(r => r.Record).OrderBy(r => r[nameof(FilterRecord.Key)]).ToListAsync();

    protected virtual async Task TestFilterAsync(
        Expression<Func<FilterRecord, bool>> filter,
        Expression<Func<Dictionary<string, object?>, bool>> dynamicFilter,
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

        // Execute the query against the vector store, once using the strongly typed filter
        // and once using the dynamic filter
        var actual = await this.GetRecords(filter, fixture.TestData.Count, new ReadOnlyMemory<float>([1, 2, 3]));

        if (actual.Count != expected.Count)
        {
            Assert.Fail($"Expected {expected.Count} results, but got {actual.Count}");
        }

        foreach (var (e, a) in expected.Zip(actual, (e, a) => (e, a)))
        {
            fixture.AssertEqualFilterRecord(e, a);
        }

        if (fixture.TestDynamic)
        {
            var dynamicActual = await this.GetDynamicRecords(dynamicFilter, fixture.TestData.Count, new ReadOnlyMemory<float>([1, 2, 3]));

            if (dynamicActual.Count != expected.Count)
            {
                Assert.Fail($"Expected {expected.Count} results, but got {actual.Count}");
            }

            foreach (var (e, a) in expected.Zip(dynamicActual, (e, a) => (e, a)))
            {
                fixture.AssertEqualDynamic(e, a);
            }
        }
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

        var actual = await fixture.Collection.VectorizedSearchAsync(
                new ReadOnlyMemory<float>([1, 2, 3]),
                top: fixture.TestData.Count,
                new()
                {
                    OldFilter = legacyFilter
                })
            .Select(r => r.Record).OrderBy(r => r.Key).ToListAsync();

        foreach (var (e, a) in expected.Zip(actual, (e, a) => (e, a)))
        {
            fixture.AssertEqualFilterRecord(e, a);
        }
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
        public override string CollectionName => "FilterTests";

        protected virtual ReadOnlyMemory<float> GetVector(int count)
            // All records have the same vector - this fixture is about testing criteria filtering only
            // Derived types may override this to provide different vectors for different records.
            => new(Enumerable.Range(1, count).Select(i => (float)i).ToArray());

        public virtual IVectorStoreRecordCollection<object, Dictionary<string, object?>> DynamicCollection { get; protected set; } = null!;

        public virtual bool TestDynamic => true;

        public override async Task InitializeAsync()
        {
            await base.InitializeAsync();

            if (this.TestDynamic)
            {
                this.DynamicCollection = this.TestStore.DefaultVectorStore.GetCollection<object, Dictionary<string, object?>>(this.CollectionName, this.GetRecordDefinition());
            }
        }

        public override VectorStoreRecordDefinition GetRecordDefinition()
            => new()
            {
                Properties =
                [
                    new VectorStoreRecordKeyProperty(nameof(FilterRecord.Key), typeof(TKey)),
                    new VectorStoreRecordVectorProperty(nameof(FilterRecord.Vector), typeof(ReadOnlyMemory<float>?), 3)
                    {
                        DistanceFunction = this.DistanceFunction,
                        IndexKind = this.IndexKind
                    },

                    new VectorStoreRecordDataProperty(nameof(FilterRecord.Int), typeof(int)) { IsIndexed = true },
                    new VectorStoreRecordDataProperty(nameof(FilterRecord.String), typeof(string)) { IsIndexed = true },
                    new VectorStoreRecordDataProperty(nameof(FilterRecord.Bool), typeof(bool)) { IsIndexed = true },
                    new VectorStoreRecordDataProperty(nameof(FilterRecord.Int2), typeof(int)) { IsIndexed = true },
                    new VectorStoreRecordDataProperty(nameof(FilterRecord.StringArray), typeof(string[])) { IsIndexed = true },
                    new VectorStoreRecordDataProperty(nameof(FilterRecord.StringList), typeof(List<string>)) { IsIndexed = true }
                ]
            };

        protected override List<FilterRecord> BuildTestData()
        {
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
                    Vector = this.GetVector(3)
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
                    Vector = this.GetVector(3)
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
                    Vector = this.GetVector(3)
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
                    Vector = this.GetVector(3)
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
                    Vector = this.GetVector(3)
                }
            ];
        }

        public virtual void AssertEqualFilterRecord(FilterRecord x, FilterRecord y)
        {
            var definitionProperties = this.GetRecordDefinition().Properties;

            Assert.Equal(x.Key, y.Key);
            Assert.Equal(x.Int, y.Int);
            Assert.Equal(x.String, y.String);
            Assert.Equal(x.Int2, y.Int2);

            if (definitionProperties.Any(p => p.DataModelPropertyName == nameof(FilterRecord.Bool)))
            {
                Assert.Equal(x.Bool, y.Bool);
            }

            if (definitionProperties.Any(p => p.DataModelPropertyName == nameof(FilterRecord.StringArray)))
            {
                Assert.Equivalent(x.StringArray, y.StringArray);
            }

            if (definitionProperties.Any(p => p.DataModelPropertyName == nameof(FilterRecord.StringList)))
            {
                Assert.Equivalent(x.StringList, y.StringList);
            }
        }

        public virtual void AssertEqualDynamic(FilterRecord x, Dictionary<string, object?> y)
        {
            var definitionProperties = this.GetRecordDefinition().Properties;

            Assert.Equal(x.Key, y["Key"]);
            Assert.Equal(x.Int, y["Int"]);
            Assert.Equal(x.String, y["String"]);
            Assert.Equal(x.Int2, y["Int2"]);

            if (definitionProperties.Any(p => p.DataModelPropertyName == nameof(FilterRecord.Bool)))
            {
                Assert.Equal(x.Bool, y["Bool"]);
            }

            if (definitionProperties.Any(p => p.DataModelPropertyName == nameof(FilterRecord.StringArray)))
            {
                Assert.Equivalent(x.StringArray, y["StringArray"]);
            }

            if (definitionProperties.Any(p => p.DataModelPropertyName == nameof(FilterRecord.StringList)))
            {
                Assert.Equivalent(x.StringList, y["StringList"]);
            }
        }

        // In some databases (Azure AI Search), the data shows up but the filtering index isn't yet updated,
        // so filtered searches show empty results. Add a filter to the seed data check below.
        protected override Task WaitForDataAsync()
            => this.TestStore.WaitForDataAsync(this.Collection, recordCount: this.TestData.Count, r => r.Int > 0);
    }
}
