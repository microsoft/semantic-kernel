// Copyright (c) Microsoft. All rights reserved.

using System.Linq.Expressions;
using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

#pragma warning disable CS8605 // Unboxing a possibly null value.
#pragma warning disable CS0252 // Possible unintended reference comparison; left hand side needs cast
#pragma warning disable RCS1098 // Constant values should be placed on right side of comparisons

namespace VectorData.ConformanceTests.Filter;

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
    public virtual Task Equal_with_string_sql_injection_in_value()
    {
        string sqlInjection = $"foo; DROP TABLE {fixture.Collection.Name};";

        return this.TestFilterAsync(
            r => r.String == sqlInjection,
            r => r["String"] == sqlInjection,
            expectZeroResults: true);
    }

    [ConditionalFact]
    public virtual async Task Equal_with_string_sql_injection_in_name()
    {
        if (fixture.TestDynamic)
        {
            await Assert.ThrowsAsync<InvalidOperationException>(
                () => this.GetDynamicRecords(r => r["String = \"not\"; DROP TABLE FilterTests;"] == "",
            fixture.TestData.Count, new ReadOnlyMemory<float>([1, 2, 3])));
        }
    }

    [ConditionalFact]
    public virtual Task Equal_with_string_containing_special_characters()
        => this.TestFilterAsync(
            r => r.String == fixture.SpecialCharactersText,
            r => r["String"] == fixture.SpecialCharactersText);

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
    public virtual Task Equal_int_property_with_nonnull_nullable_int()
    {
        int? i = 8;

        return this.TestFilterAsync(
            r => r.Int == i,
            r => (int)r["Int"] == i);
    }

    [ConditionalFact]
    public virtual Task Equal_int_property_with_null_nullable_int()
    {
        int? i = null;

        return this.TestFilterAsync(
            r => r.Int == i,
            r => (int)r["Int"] == i,
            expectZeroResults: true);
    }

    [ConditionalFact]
    public virtual Task Equal_int_property_with_nonnull_nullable_int_Value()
    {
        int? i = 8;

        return this.TestFilterAsync(
            r => r.Int == i.Value,
            r => (int)r["Int"] == i.Value);
    }

#pragma warning disable CS8629 // Nullable value type may be null.
    [ConditionalFact]
    public virtual async Task Equal_int_property_with_null_nullable_int_Value()
    {
        int? i = null;

        // TODO: Some connectors wrap filter translation exceptions in a VectorStoreException (#11766)
        var exception = await Assert.ThrowsAnyAsync<Exception>(() => this.TestFilterAsync(
            r => r.Int == i.Value,
            r => (int)r["Int"] == i.Value,
            expectZeroResults: true));

        if (exception is not InvalidOperationException and not VectorStoreException { InnerException: InvalidOperationException })
        {
            Assert.Fail($"Expected {nameof(InvalidOperationException)} or {nameof(VectorStoreException)} but got {exception.GetType()}");
        }
    }
#pragma warning restore CS8629

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

    #region Variable types

    [ConditionalFact]
    public virtual Task Captured_local_variable()
    {
        // ReSharper disable once ConvertToConstant.Local
        var i = 8;

        return this.TestFilterAsync(
            r => r.Int == i,
            r => (int)r["Int"] == i);
    }

    [ConditionalFact]
    public virtual Task Member_field()
        => this.TestFilterAsync(
            r => r.Int == this._memberField,
            r => (int)r["Int"] == this._memberField);

    [ConditionalFact]
    public virtual Task Member_readonly_field()
        => this.TestFilterAsync(
            r => r.Int == this._memberReadOnlyField,
            r => (int)r["Int"] == this._memberReadOnlyField);

    [ConditionalFact]
    public virtual Task Member_static_field()
        => this.TestFilterAsync(
            r => r.Int == _staticMemberField,
            r => (int)r["Int"] == _staticMemberField);

    [ConditionalFact]
    public virtual Task Member_static_readonly_field()
        => this.TestFilterAsync(
            r => r.Int == _staticMemberReadOnlyField,
            r => (int)r["Int"] == _staticMemberReadOnlyField);

    [ConditionalFact]
    public virtual Task Member_nested_access()
        => this.TestFilterAsync(
            r => r.Int == this._someWrapper.SomeWrappedValue,
            r => (int)r["Int"] == this._someWrapper.SomeWrappedValue);

#pragma warning disable RCS1169 // Make field read-only
#pragma warning disable IDE0044 // Make field read-only
#pragma warning disable RCS1187 // Use constant instead of field
#pragma warning disable CA1802 // Use literals where appropriate
    private int _memberField = 8;
    private readonly int _memberReadOnlyField = 8;

    private static int _staticMemberField = 8;
    private static readonly int _staticMemberReadOnlyField = 8;

    private SomeWrapper _someWrapper = new();
#pragma warning restore CA1802
#pragma warning restore RCS1187
#pragma warning restore RCS1169
#pragma warning restore IDE0044

    private sealed class SomeWrapper
    {
        public int SomeWrappedValue = 8;
    }

    #endregion Variable types

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
        => await fixture.Collection.SearchAsync(
                vector,
                top: top,
                new() { Filter = filter })
            .Select(r => r.Record).OrderBy(r => r.Key).ToListAsync();

    protected virtual async Task<List<Dictionary<string, object?>>> GetDynamicRecords(
        Expression<Func<Dictionary<string, object?>, bool>> dynamicFilter, int top, ReadOnlyMemory<float> vector)
        => await fixture.DynamicCollection.SearchAsync(
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
            Assert.Fail("The test returns zero results, and so may be unreliable");
        }
        else if (expectZeroResults && expected.Count != 0)
        {
            Assert.Fail($"{nameof(expectZeroResults)} was true, but the test returned {expected.Count} results.");
        }

        if (expected.Count == fixture.TestData.Count && !expectAllResults)
        {
            Assert.Fail("The test returns all results, and so may be unreliable");
        }
        else if (expectAllResults && expected.Count != fixture.TestData.Count)
        {
            Assert.Fail($"{nameof(expectAllResults)} was true, but the test returned {expected.Count} results instead of the expected {fixture.TestData.Count}.");
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

        var actual = await fixture.Collection.SearchAsync(
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

        public virtual string SpecialCharactersText => """>with $om[ specia]"chara<ters'and\stuff""";

        protected virtual ReadOnlyMemory<float> GetVector(int count)
            // All records have the same vector - this fixture is about testing criteria filtering only
            // Derived types may override this to provide different vectors for different records.
            => new(Enumerable.Range(1, count).Select(i => (float)i).ToArray());

        public virtual VectorStoreCollection<object, Dictionary<string, object?>> DynamicCollection { get; protected set; } = null!;

        public virtual bool TestDynamic => true;

        public override async Task InitializeAsync()
        {
            await base.InitializeAsync();

            if (this.TestDynamic)
            {
                this.DynamicCollection = this.TestStore.DefaultVectorStore.GetDynamicCollection(this.CollectionName, this.CreateRecordDefinition());
            }
        }

        public override VectorStoreCollectionDefinition CreateRecordDefinition()
            => new()
            {
                Properties =
                [
                    new VectorStoreKeyProperty(nameof(FilterRecord.Key), typeof(TKey)),
                    new VectorStoreVectorProperty(nameof(FilterRecord.Vector), typeof(ReadOnlyMemory<float>?), 3)
                    {
                        DistanceFunction = this.DistanceFunction,
                        IndexKind = this.IndexKind
                    },

                    new VectorStoreDataProperty(nameof(FilterRecord.Int), typeof(int)) { IsIndexed = true },
                    new VectorStoreDataProperty(nameof(FilterRecord.String), typeof(string)) { IsIndexed = true },
                    new VectorStoreDataProperty(nameof(FilterRecord.Bool), typeof(bool)) { IsIndexed = true },
                    new VectorStoreDataProperty(nameof(FilterRecord.Int2), typeof(int)) { IsIndexed = true },
                    new VectorStoreDataProperty(nameof(FilterRecord.StringArray), typeof(string[])) { IsIndexed = true },
                    new VectorStoreDataProperty(nameof(FilterRecord.StringList), typeof(List<string>)) { IsIndexed = true }
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
                    String = this.SpecialCharactersText,
                    Int2 = 101,
                    StringArray = ["y", "z"],
                    StringList = ["y", "z"],
                    Vector = this.GetVector(3)
                }
            ];
        }

        public virtual void AssertEqualFilterRecord(FilterRecord x, FilterRecord y)
        {
            var definitionProperties = this.CreateRecordDefinition().Properties;

            Assert.Equal(x.Key, y.Key);
            Assert.Equal(x.Int, y.Int);
            Assert.Equal(x.String, y.String);
            Assert.Equal(x.Int2, y.Int2);

            if (definitionProperties.Any(p => p.Name == nameof(FilterRecord.Bool)))
            {
                Assert.Equal(x.Bool, y.Bool);
            }

            if (definitionProperties.Any(p => p.Name == nameof(FilterRecord.StringArray)))
            {
                Assert.Equivalent(x.StringArray, y.StringArray);
            }

            if (definitionProperties.Any(p => p.Name == nameof(FilterRecord.StringList)))
            {
                Assert.Equivalent(x.StringList, y.StringList);
            }
        }

        public virtual void AssertEqualDynamic(FilterRecord x, Dictionary<string, object?> y)
        {
            var definitionProperties = this.CreateRecordDefinition().Properties;

            Assert.Equal(x.Key, y["Key"]);
            Assert.Equal(x.Int, y["Int"]);
            Assert.Equal(x.String, y["String"]);
            Assert.Equal(x.Int2, y["Int2"]);

            if (definitionProperties.Any(p => p.Name == nameof(FilterRecord.Bool)))
            {
                Assert.Equal(x.Bool, y["Bool"]);
            }

            if (definitionProperties.Any(p => p.Name == nameof(FilterRecord.StringArray)))
            {
                Assert.Equivalent(x.StringArray, y["StringArray"]);
            }

            if (definitionProperties.Any(p => p.Name == nameof(FilterRecord.StringList)))
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
