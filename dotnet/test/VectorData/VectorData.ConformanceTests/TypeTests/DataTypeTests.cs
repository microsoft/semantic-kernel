// Copyright (c) Microsoft. All rights reserved.

using System.Linq.Expressions;
using System.Reflection;
using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace VectorData.ConformanceTests.TypeTests;

public abstract class DataTypeTests<TKey, TRecord>(DataTypeTests<TKey, TRecord>.Fixture fixture) : DataTypeTests<TKey>()
    where TKey : notnull
    where TRecord : DataTypeTests<TKey>.RecordBase, new()
{
    // Note: nullable value types are tested automatically within TestTypeStructAsync

    [ConditionalFact]
    public virtual Task Byte()
        => fixture.UnsupportedDefaultTypes.Contains(typeof(byte))
            ? Task.CompletedTask
            : this.Test<byte>("Byte", 8, 9);

    [ConditionalFact]
    public virtual Task Short()
        => fixture.UnsupportedDefaultTypes.Contains(typeof(short))
            ? Task.CompletedTask
            : this.Test<short>("Short", 8, 9);

    [ConditionalFact]
    public virtual Task Int()
        => fixture.UnsupportedDefaultTypes.Contains(typeof(int))
            ? Task.CompletedTask
            : this.Test<int>("Int", 8, 9);

    [ConditionalFact]
    public virtual Task Long()
        => fixture.UnsupportedDefaultTypes.Contains(typeof(long))
            ? Task.CompletedTask
            : this.Test<long>("Long", 8L, 9L);

    [ConditionalFact]
    public virtual Task Float()
        => fixture.UnsupportedDefaultTypes.Contains(typeof(float))
            ? Task.CompletedTask
            : this.Test<float>("Float", 8.5f, 9.5f);

    [ConditionalFact]
    public virtual Task Double()
        => fixture.UnsupportedDefaultTypes.Contains(typeof(double))
            ? Task.CompletedTask
            : this.Test<double>("Double", 8.5d, 9.5d);

    [ConditionalFact]
    public virtual Task Decimal()
        => fixture.UnsupportedDefaultTypes.Contains(typeof(decimal))
            ? Task.CompletedTask
            : this.Test<decimal>("Decimal", 8.5m, 9.5m);

    [ConditionalFact]
    public virtual Task String()
        => fixture.UnsupportedDefaultTypes.Contains(typeof(string))
            ? Task.CompletedTask
            : this.Test<string>("String", "foo", "bar");

    [ConditionalFact]
    public virtual Task Bool()
        => fixture.UnsupportedDefaultTypes.Contains(typeof(bool))
            ? Task.CompletedTask
            : this.Test<bool>("Bool", true, false);

    [ConditionalFact]
    public virtual Task Guid()
        => fixture.UnsupportedDefaultTypes.Contains(typeof(Guid))
            ? Task.CompletedTask
            : this.Test<Guid>(
                "Guid",
                new Guid("603840bf-cf91-4521-8b8e-8b6a2e75910a"),
                new Guid("e9a97807-8cf0-4741-8ce3-82df676ca0f0"));

    [ConditionalFact]
    public virtual Task DateTime()
        => fixture.UnsupportedDefaultTypes.Contains(typeof(DateTime))
            ? Task.CompletedTask
            : this.Test<DateTime>(
                "DateTime",
                new DateTime(2020, 1, 1, 12, 30, 45),
                new DateTime(2021, 2, 3, 13, 40, 55),
                instantiationExpression: () => new DateTime(2020, 1, 1, 12, 30, 45));

    [ConditionalFact]
    public virtual Task DateTimeOffset()
        => fixture.UnsupportedDefaultTypes.Contains(typeof(DateTimeOffset))
            ? Task.CompletedTask
            : this.Test<DateTimeOffset>(
                "DateTimeOffset",
                new DateTimeOffset(2020, 1, 1, 12, 30, 45, TimeSpan.FromHours(2)),
                new DateTimeOffset(2021, 2, 3, 13, 40, 55, TimeSpan.FromHours(3)),
                instantiationExpression: () => new DateTimeOffset(2020, 1, 1, 12, 30, 45, TimeSpan.FromHours(2)));

    [ConditionalFact]
    public virtual Task DateOnly()
    {
#if NET8_0_OR_GREATER
        return fixture.UnsupportedDefaultTypes.Contains(typeof(DateOnly))
            ? Task.CompletedTask
            : this.Test<DateOnly>(
                "DateOnly",
                new DateOnly(2020, 1, 1),
                new DateOnly(2021, 2, 3));
#else
        return Task.CompletedTask;
#endif
    }

    [ConditionalFact]
    public virtual Task TimeOnly()
    {
#if NET8_0_OR_GREATER
        return fixture.UnsupportedDefaultTypes.Contains(typeof(TimeOnly))
            ? Task.CompletedTask
            : this.Test<TimeOnly>(
                "TimeOnly",
                new TimeOnly(12, 30, 45),
                new TimeOnly(13, 40, 55));
#else
        return Task.CompletedTask;
#endif
    }

    [ConditionalFact]
    public virtual Task String_array()
        => fixture.UnsupportedDefaultTypes.Contains(typeof(string[]))
            ? Task.CompletedTask
            : this.Test<string[]>(
                "StringArray",
                ["foo", "bar"],
                ["foo", "baz"]);

    [ConditionalFact]
    public virtual Task Nullable_value_type()
        => fixture.UnsupportedDefaultTypes.Contains(typeof(int?))
            ? Task.CompletedTask
            : this.Test<int?>("NullableInt", 8, 9);

    protected virtual async Task Test<TTestType>(
        string propertyName,
        TTestType mainValue,
        TTestType otherValue,
        bool isFilterable = true,
        Action<TTestType, TTestType>? comparisonAction = null,
        Expression<Func<TTestType>>? instantiationExpression = null)
    {
        if (propertyName is "Key" or "Vector")
        {
            throw new ArgumentException($"The property name '{propertyName}' is reserved and cannot be used for testing.", nameof(propertyName));
        }

        var property = typeof(TRecord).GetProperty(propertyName)
            ?? throw new ArgumentException($"The type '{typeof(TRecord).Name}' does not have a property named '{propertyName}'.", nameof(propertyName));
        comparisonAction ??= (a, b) => Assert.Equal(a, b);
        var instantiationExpressionBody = instantiationExpression is null
            ? Expression.Constant(mainValue, typeof(TTestType))
            : instantiationExpression.Body;

        await fixture.Collection.DeleteAsync([fixture.MainRecordKey, fixture.OtherRecordKey, fixture.NullRecordKey]);
        await fixture.TestStore.WaitForDataAsync(fixture.Collection, recordCount: 0);

        // Step 1: Insert data
        await this.InsertData(property, mainValue, otherValue);

        // Step 2: Read the values back via GetAsync
        TRecord result = await fixture.Collection.GetAsync(fixture.MainRecordKey) ?? throw new InvalidOperationException($"Record with key '{fixture.MainRecordKey}' was not found.");
        comparisonAction(mainValue, (TTestType)property.GetValue(result)!);

        // Step 3: Exercise filtering by the value, using a constant in the filter expression
        if (isFilterable)
        {
            await this.TestFiltering(fixture.Collection, property, mainValue, comparisonAction, instantiationExpressionBody);
        }

        ///////////////////////
        // Test dynamic mapping
        ///////////////////////
        if (fixture.RecreateCollection)
        {
            await fixture.Collection.EnsureCollectionDeletedAsync();
        }
        else
        {
            await fixture.Collection.DeleteAsync([fixture.MainRecordKey, fixture.OtherRecordKey, fixture.NullRecordKey]);
            await fixture.TestStore.WaitForDataAsync(fixture.Collection, recordCount: 0);
        }

        var dynamicCollection = fixture.VectorStore.GetDynamicCollection(fixture.CollectionName, fixture.CreateRecordDefinition());

        if (fixture.RecreateCollection)
        {
            await dynamicCollection.EnsureCollectionExistsAsync();
        }

        // Step 1: Insert data
        await this.InsertDynamicData(dynamicCollection, propertyName, mainValue, otherValue);

        // Step 2: Read the values back via GetAsync
        var dynamicResult = await dynamicCollection.GetAsync(fixture.MainRecordKey) ?? throw new InvalidOperationException($"Record with key '{fixture.MainRecordKey}' was not found.");
        comparisonAction(mainValue, (TTestType)dynamicResult[propertyName]!);

        // Step 3: Exercise dynamic filtering by the value, using a constant in the filter expression
        if (isFilterable)
        {
            await this.TestDynamicFiltering(dynamicCollection, propertyName, mainValue, comparisonAction, instantiationExpressionBody);
        }
    }

    private async Task InsertData<TTestType>(PropertyInfo property, TTestType mainValue, TTestType otherValue)
    {
        // Note that all records have the same vector
        var mainRecord = GenerateEmptyRecord();
        mainRecord.Key = fixture.MainRecordKey;
        mainRecord.Vector = fixture.Vector;
        property.SetValue(mainRecord, mainValue);

        var otherRecord = GenerateEmptyRecord();
        otherRecord.Key = fixture.OtherRecordKey;
        otherRecord.Vector = fixture.Vector;
        property.SetValue(otherRecord, otherValue);

        List<TRecord> testData = [mainRecord, otherRecord];

        if (default(TTestType) == null && fixture.IsNullSupported)
        {
            var nullRecord = GenerateEmptyRecord();
            nullRecord.Key = fixture.NullRecordKey;
            nullRecord.Vector = fixture.Vector;
            property.SetValue(nullRecord, null);
            testData.Add(nullRecord);
        }

        await fixture.Collection.UpsertAsync(testData);
        await fixture.TestStore.WaitForDataAsync(fixture.Collection, recordCount: testData.Count);

        TRecord GenerateEmptyRecord()
        {
            var record = new TRecord();

            foreach (var property in fixture.CreateRecordDefinition().Properties)
            {
                var propertyInfo = typeof(TRecord).GetProperty(property.Name)
                    ?? throw new InvalidOperationException($"Property '{property.Name}' not found on record type '{typeof(TRecord).Name}'.");
                propertyInfo.SetValue(record, this.GenerateEmptyProperty(property));
            }

            return record;
        }
    }

    private async Task InsertDynamicData<TTestType>(
        VectorStoreCollection<object, Dictionary<string, object?>> dynamicCollection,
        string propertyName,
        TTestType mainValue,
        TTestType otherValue)
    {
        // Note that all records have the same vector
        var mainRecord = GenerateEmptyRecord();
        mainRecord[nameof(RecordBase.Key)] = fixture.MainRecordKey;
        mainRecord[nameof(RecordBase.Vector)] = fixture.Vector;
        mainRecord[propertyName] = mainValue;

        var otherRecord = GenerateEmptyRecord();
        otherRecord[nameof(RecordBase.Key)] = fixture.OtherRecordKey;
        otherRecord[nameof(RecordBase.Vector)] = fixture.Vector;
        otherRecord[propertyName] = otherValue;

        List<Dictionary<string, object?>> testData = [mainRecord, otherRecord];

        if (default(TTestType) == null && fixture.IsNullSupported)
        {
            var nullRecord = GenerateEmptyRecord();
            nullRecord[nameof(RecordBase.Key)] = fixture.NullRecordKey;
            nullRecord[nameof(RecordBase.Vector)] = fixture.Vector;
            nullRecord[propertyName] = null;
            testData.Add(nullRecord);
        }

        await dynamicCollection.UpsertAsync(testData);
        await fixture.TestStore.WaitForDataAsync(dynamicCollection, recordCount: testData.Count);

        Dictionary<string, object?> GenerateEmptyRecord()
        {
            var record = new Dictionary<string, object?>();

            foreach (var property in fixture.CreateRecordDefinition().Properties)
            {
                record[property.Name] = this.GenerateEmptyProperty(property);
            }

            return record;
        }
    }

    protected virtual object? GenerateEmptyProperty(VectorStoreProperty property)
        => property.Type switch
        {
            null => throw new InvalidOperationException($"Property '{property.Name}' has no type defined."),

            // For value types, we create an instance with the default value.
            // This is necessary for relational providers where non-nullable columns are created.
            var t when t.IsValueType => Activator.CreateInstance(t),

            // In some cases (Azure AI Search), array fields must be non-null
            var t when t.IsArray => Array.CreateInstance(t.GetElementType()!, 0),

            _ => null
        };

    private async Task TestFiltering<TTestType>(
        VectorStoreCollection<TKey, TRecord> collection,
        PropertyInfo property,
        TTestType mainValue,
        Action<TTestType, TTestType> comparisonAction,
        Expression instantiationExpression)
    {
        // Note: we need to manually build the expression tree since the equality operator can't be used over
        // unconstrained generic types.
        var lambdaParameter = Expression.Parameter(typeof(TRecord), "r");
        var filter = Expression.Lambda<Func<TRecord, bool>>(
            Expression.Equal(
                Expression.Property(lambdaParameter, property),
                instantiationExpression),
            lambdaParameter);

        // Some databases (Mongo) update the filter index asynchronously, so we wait until the record appears under the filter,
        // and then do the main search to make sure only the main record is returned.
        await fixture.TestStore.WaitForDataAsync(collection, filter: filter, recordCount: 1);
        var result = (await collection.SearchAsync(fixture.Vector, top: 100, new() { Filter = filter }).SingleAsync()).Record;

        Assert.Equal(fixture.MainRecordKey, result.Key);
        comparisonAction(mainValue, (TTestType)property.GetValue(result)!);

        // Exercise filtering by a null value
        if (default(TTestType) == null && fixture.IsNullFilteringSupported)
        {
            lambdaParameter = Expression.Parameter(typeof(TRecord), "r");
            filter = Expression.Lambda<Func<TRecord, bool>>(
                Expression.Equal(
                    Expression.Property(lambdaParameter, property),
                    Expression.Constant(null, typeof(TTestType))),
                lambdaParameter);

            result = (await collection.SearchAsync(fixture.Vector, top: 100, new() { Filter = filter }).SingleAsync()).Record;

            Assert.Equal(fixture.NullRecordKey, result.Key);
        }
    }

    private async Task TestDynamicFiltering<TTestType>(
        VectorStoreCollection<object, Dictionary<string, object?>> dynamicCollection,
        string propertyName,
        TTestType mainValue,
        Action<TTestType, TTestType> comparisonAction,
        Expression instantiationExpression)
    {
        // Note: we need to manually build the expression tree since we want the property name to be a constant
        var lambdaParameter = Expression.Parameter(typeof(Dictionary<string, object>), "r");
        var filter = Expression.Lambda<Func<Dictionary<string, object?>, bool>>(
            Expression.Equal(
                Expression.Convert(
                    Expression.Call(lambdaParameter, DynamicDictionaryIndexer, Expression.Constant(propertyName)),
                    typeof(TTestType)),
                instantiationExpression),
            lambdaParameter);

        // Some databases (Mongo) update the filter index asynchronously, so we wait until the record appears under the filter,
        // and then do the main search to make sure only the main record is returned.
        await fixture.TestStore.WaitForDataAsync(dynamicCollection, filter: filter, recordCount: 1);
        var result = (await dynamicCollection.SearchAsync(fixture.Vector, top: 100, new() { Filter = filter }).SingleAsync()).Record;
        Assert.Equal(fixture.MainRecordKey, result[nameof(RecordBase.Key)]);
        comparisonAction(mainValue, (TTestType)result[propertyName]!);

        // Exercise filtering by a null value
        if (default(TTestType) == null && fixture.IsNullFilteringSupported)
        {
            lambdaParameter = Expression.Parameter(typeof(Dictionary<string, object?>), "r");
            filter = Expression.Lambda<Func<Dictionary<string, object?>, bool>>(
                Expression.Equal(
                Expression.Convert(
                    Expression.Call(lambdaParameter, DynamicDictionaryIndexer, Expression.Constant(propertyName)),
                    typeof(TTestType)),
                    Expression.Constant(null, typeof(TTestType))),
                lambdaParameter);

            result = (await dynamicCollection.SearchAsync(fixture.Vector, top: 100, new() { Filter = filter }).SingleAsync()).Record;

            Assert.Equal(fixture.NullRecordKey, result[nameof(RecordBase.Key)]);
        }
    }

    private static readonly MethodInfo DynamicDictionaryIndexer = typeof(Dictionary<string, object?>).GetMethod("get_Item")!;

    public abstract class Fixture : VectorStoreCollectionFixture<TKey, TRecord>
    {
        public override string CollectionName => "DataTypeTests";

        public virtual bool IsNullSupported => true;
        public virtual bool IsNullFilteringSupported => true;

        public virtual Type[] UnsupportedDefaultTypes { get; } = [];

        public virtual TKey MainRecordKey { get; protected set; } = default!;
        public virtual TKey OtherRecordKey { get; protected set; } = default!;
        public virtual TKey NullRecordKey { get; protected set; } = default!;

        public virtual float[] Vector { get; } = [1, 2, 3];

        private readonly IList<VectorStoreDataProperty> _defaultDataProperties = null!;

        /// <summary>
        /// Whether the recreate the collection while testing, as opposed to deleting the records.
        /// Necessary for InMemory, where the .NET mapped on the collection cannot be changed.
        /// </summary>
        public virtual bool RecreateCollection => false;

#pragma warning disable CA2214 // Do not call overridable methods in constructors
        protected Fixture()
        {
            this._defaultDataProperties = this.GetDataProperties();
        }
#pragma warning restore CA2214

        public override async Task InitializeAsync()
        {
            await base.InitializeAsync();

            this.MainRecordKey = this.GenerateNextKey<TKey>();
            this.OtherRecordKey = this.GenerateNextKey<TKey>();
            this.NullRecordKey = this.GenerateNextKey<TKey>();
        }

        public override VectorStoreCollectionDefinition CreateRecordDefinition()
            => new()
            {
                Properties =
                [
                    new VectorStoreKeyProperty(nameof(RecordBase.Key), typeof(TKey)),
                    new VectorStoreVectorProperty(nameof(RecordBase.Vector), typeof(float[]), 3)
                    {
                        DistanceFunction = this.DistanceFunction,
                        IndexKind = this.IndexKind
                    },

                    .. this._defaultDataProperties
                ]
            };

        public virtual IList<VectorStoreDataProperty> GetDataProperties()
        {
            var properties = new List<VectorStoreDataProperty>();

            if (!this.UnsupportedDefaultTypes.Contains(typeof(byte)))
            {
                properties.Add(new VectorStoreDataProperty(nameof(DefaultRecord.Byte), typeof(byte)) { IsIndexed = true });
            }

            if (!this.UnsupportedDefaultTypes.Contains(typeof(short)))
            {
                properties.Add(new VectorStoreDataProperty(nameof(DefaultRecord.Short), typeof(short)) { IsIndexed = true });
            }

            if (!this.UnsupportedDefaultTypes.Contains(typeof(int)))
            {
                properties.Add(new VectorStoreDataProperty(nameof(DefaultRecord.Int), typeof(int)) { IsIndexed = true });
            }

            if (!this.UnsupportedDefaultTypes.Contains(typeof(long)))
            {
                properties.Add(new VectorStoreDataProperty(nameof(DefaultRecord.Long), typeof(long)) { IsIndexed = true });
            }

            if (!this.UnsupportedDefaultTypes.Contains(typeof(float)))
            {
                properties.Add(new VectorStoreDataProperty(nameof(DefaultRecord.Float), typeof(float)) { IsIndexed = true });
            }

            if (!this.UnsupportedDefaultTypes.Contains(typeof(double)))
            {
                properties.Add(new VectorStoreDataProperty(nameof(DefaultRecord.Double), typeof(double)) { IsIndexed = true });
            }

            if (!this.UnsupportedDefaultTypes.Contains(typeof(decimal)))
            {
                properties.Add(new VectorStoreDataProperty(nameof(DefaultRecord.Decimal), typeof(decimal)) { IsIndexed = true });
            }

            if (!this.UnsupportedDefaultTypes.Contains(typeof(string)))
            {
                properties.Add(new VectorStoreDataProperty(nameof(DefaultRecord.String), typeof(string)) { IsIndexed = true });
            }

            if (!this.UnsupportedDefaultTypes.Contains(typeof(bool)))
            {
                properties.Add(new VectorStoreDataProperty(nameof(DefaultRecord.Bool), typeof(bool)) { IsIndexed = true });
            }

            if (!this.UnsupportedDefaultTypes.Contains(typeof(Guid)))
            {
                properties.Add(new VectorStoreDataProperty(nameof(DefaultRecord.Guid), typeof(Guid)) { IsIndexed = true });
            }

            if (!this.UnsupportedDefaultTypes.Contains(typeof(DateTime)))
            {
                properties.Add(new VectorStoreDataProperty(nameof(DefaultRecord.DateTime), typeof(DateTime)) { IsIndexed = true });
            }

            if (!this.UnsupportedDefaultTypes.Contains(typeof(DateTimeOffset)))
            {
                properties.Add(new VectorStoreDataProperty(nameof(DefaultRecord.DateTimeOffset), typeof(DateTimeOffset)) { IsIndexed = true });
            }

#if NET8_0_OR_GREATER
            if (!this.UnsupportedDefaultTypes.Contains(typeof(DateOnly)))
            {
                properties.Add(new VectorStoreDataProperty(nameof(DefaultRecord.DateOnly), typeof(DateOnly)) { IsIndexed = true });
            }

            if (!this.UnsupportedDefaultTypes.Contains(typeof(TimeOnly)))
            {
                properties.Add(new VectorStoreDataProperty(nameof(DefaultRecord.TimeOnly), typeof(TimeOnly)) { IsIndexed = true });
            }
#endif
            if (!this.UnsupportedDefaultTypes.Contains(typeof(string[])))
            {
                properties.Add(new VectorStoreDataProperty(nameof(DefaultRecord.StringArray), typeof(string[])) { IsIndexed = true });
            }

            if (!this.UnsupportedDefaultTypes.Contains(typeof(int?)))
            {
                properties.Add(new VectorStoreDataProperty(nameof(DefaultRecord.NullableInt), typeof(int?)) { IsIndexed = true });
            }

            return properties;
        }
    }
}

// We have this base class so the Record type can be referenced in subtypes (the main TypeTests class
// is generic over the record type as well).
public abstract class DataTypeTests<TKey>()
    where TKey : notnull
{
    public class RecordBase : TestRecord<TKey>
    {
        public float[] Vector { get; set; } = default!;
    }

    public class DefaultRecord : RecordBase
    {
        public byte Byte { get; set; }
        public short Short { get; set; }
        public int Int { get; set; }
        public long Long { get; set; }

        public float Float { get; set; }
        public double Double { get; set; }
        public decimal Decimal { get; set; }

        public string? String { get; set; }
        public bool Bool { get; set; }
        public Guid Guid { get; set; }

        public DateTime DateTime { get; set; }
        public DateTimeOffset DateTimeOffset { get; set; }

#if NET8_0_OR_GREATER
        public DateOnly DateOnly { get; set; }
        public TimeOnly TimeOnly { get; set; }
#endif

        public string[] StringArray { get; set; } = null!;

        public int? NullableInt { get; set; }
    }
}
