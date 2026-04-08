// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace VectorData.ConformanceTests.ModelTests;

public abstract class DynamicModelTests<TKey>(DynamicModelTests<TKey>.Fixture fixture) : IAsyncLifetime
    where TKey : notnull
{
    #region Get

    [ConditionalTheory, MemberData(nameof(IncludeVectorsData))]
    public virtual async Task GetAsync_single_record(bool includeVectors)
    {
        var expectedRecord = fixture.TestData[0];

        var received = await fixture.Collection.GetAsync(
            (TKey)expectedRecord[KeyPropertyName]!,
            new() { IncludeVectors = includeVectors });

        AssertEquivalent(expectedRecord, received, includeVectors, fixture.TestStore.VectorsComparable);
    }

    [ConditionalTheory, MemberData(nameof(IncludeVectorsData))]
    public virtual async Task GetAsync_multiple_records(bool includeVectors)
    {
        var expectedRecords = fixture.TestData.Take(2);
        var ids = expectedRecords.Select(record => record[KeyPropertyName]!);

        var received = await fixture.Collection.GetAsync(ids, new() { IncludeVectors = includeVectors }).ToArrayAsync();

        foreach (var record in expectedRecords)
        {
            AssertEquivalent(
                record,
                received.Single(r => r[KeyPropertyName]!.Equals(record[KeyPropertyName])),
                includeVectors,
                fixture.TestStore.VectorsComparable);
        }
    }

    [ConditionalFact]
    public virtual async Task GetAsync_throws_for_null_key()
    {
        // Skip this test for value type keys
        if (default(TKey) is not null)
        {
            return;
        }

        ArgumentNullException ex = await Assert.ThrowsAsync<ArgumentNullException>(() => fixture.Collection.GetAsync((TKey)default!));
        Assert.Equal("key", ex.ParamName);
    }

    [ConditionalFact]
    public virtual async Task GetAsync_throws_for_null_keys()
    {
        ArgumentNullException ex = await Assert.ThrowsAsync<ArgumentNullException>(() => fixture.Collection.GetAsync(keys: null!).ToArrayAsync().AsTask());
        Assert.Equal("keys", ex.ParamName);
    }

    [ConditionalFact]
    public virtual async Task GetAsync_returns_null_for_missing_key()
    {
        TKey key = fixture.GenerateNextKey<TKey>();

        Assert.Null(await fixture.Collection.GetAsync(key));
    }

    [ConditionalFact]
    public virtual async Task GetAsync_returns_empty_for_empty_keys()
    {
        Assert.Empty(await fixture.Collection.GetAsync([]).ToArrayAsync());
    }

    [ConditionalTheory, MemberData(nameof(IncludeVectorsData))]
    public virtual async Task GetAsync_with_filter(bool includeVectors)
    {
        var expectedRecord = fixture.TestData[0];

        var results = await fixture.Collection.GetAsync(
            r => (int)r[IntegerPropertyName]! == 1,
            top: 2,
            new() { IncludeVectors = includeVectors })
            .ToListAsync();

        var receivedRecord = Assert.Single(results);
        AssertEquivalent(expectedRecord, receivedRecord, includeVectors, fixture.TestStore.VectorsComparable);
    }

    [ConditionalFact]
    public virtual async Task GetAsync_with_filter_by_true()
    {
        var count = await fixture.Collection.GetAsync(r => true, top: 100).CountAsync();
        Assert.Equal(fixture.TestData.Count, count);
        Assert.True(count < 100);
    }

    [ConditionalFact]
    public virtual async Task GetAsync_with_filter_and_OrderBy()
    {
        var ascendingNumbers = fixture.TestData
            .Where(r => (int)r[IntegerPropertyName]! > 1)
            .OrderBy(r => r[IntegerPropertyName])
            .Take(2)
            .Select(r => (int)r[IntegerPropertyName]!)
            .ToList();

        var descendingNumbers = fixture.TestData
            .Where(r => (int)r[IntegerPropertyName]! > 1)
            .OrderByDescending(r => r[IntegerPropertyName])
            .Take(2)
            .Select(r => (int)r[IntegerPropertyName]!)
            .ToList();

        // Make sure the actual results are different for ascending/descending, otherwise the test is meaningless
        Assert.NotEqual(ascendingNumbers, descendingNumbers);

        // Finally, query once with ascending and once with descending, comparing against the expected results above.
        var results = await fixture.Collection.GetAsync(
            r => (int)r[IntegerPropertyName]! > 1,
                top: 2,
                new() { OrderBy = o => o.Ascending(r => r[IntegerPropertyName]) })
            .Select(r => (int)r[IntegerPropertyName]!)
            .ToListAsync();

        Assert.Equal(ascendingNumbers, results);

        results = await fixture.Collection.GetAsync(
                r => (int)r[IntegerPropertyName]! > 1,
                top: 2,
                new() { OrderBy = o => o.Descending(r => r[IntegerPropertyName]) })
            .Select(r => (int)r[IntegerPropertyName]!)
            .ToListAsync();

        Assert.Equal(descendingNumbers, results);
    }

    [ConditionalFact]
    public virtual async Task GetAsync_with_filter_and_multiple_OrderBys()
    {
        var ascendingNumbers = fixture.TestData
            .OrderByDescending(r => r[StringPropertyName])
            .ThenBy(r => r[IntegerPropertyName])
            .Take(2)
            .Select(r => (int)r[IntegerPropertyName]!)
            .ToList();

        var descendingNumbers = fixture.TestData
            .OrderByDescending(r => r[StringPropertyName])
            .ThenByDescending(r => r[IntegerPropertyName])
            .Take(2)
            .Select(r => (int)r[IntegerPropertyName]!)
            .ToList();

        // Make sure the actual results are different for ascending/descending, otherwise the test is meaningless
        Assert.NotEqual(ascendingNumbers, descendingNumbers);

        var results = await fixture.Collection.GetAsync(
                r => true,
                top: 2,
                new() { OrderBy = o => o.Descending(r => r[StringPropertyName]).Ascending(r => r[IntegerPropertyName]) })
            .Select(r => (int)r[IntegerPropertyName]!)
            .ToListAsync();

        Assert.Equal(ascendingNumbers, results);

        results = await fixture.Collection.GetAsync(
                r => true,
                top: 2,
                new() { OrderBy = o => o.Descending(r => r[StringPropertyName]).Descending(r => r[IntegerPropertyName]) })
            .Select(r => (int)r[IntegerPropertyName]!)
            .ToListAsync();

        Assert.Equal(descendingNumbers, results);
    }

    [ConditionalFact]
    public virtual async Task GetAsync_with_filter_and_OrderBy_and_Skip()
    {
        var results = await fixture.Collection.GetAsync(
            r => (int)r[IntegerPropertyName]! > 1,
            top: 2,
            new() { OrderBy = o => o.Ascending(r => r[IntegerPropertyName]), Skip = 1 })
            .Select(r => (int)r[IntegerPropertyName]!)
            .ToListAsync();

        Assert.Equal(
            fixture.TestData
                .Where(r => (int)r[IntegerPropertyName]! > 1)
                .OrderBy(r => r[IntegerPropertyName])
                .Skip(1)
                .Take(2)
                .Select(r => (int)r[IntegerPropertyName]!),
            results);
    }

    #endregion Get

    #region Upsert

    [ConditionalFact]
    public virtual async Task Insert_single_record()
    {
        TKey expectedKey = fixture.GenerateNextKey<TKey>();
        var inserted = new Dictionary<string, object?>
        {
            [KeyPropertyName] = expectedKey,
            [StringPropertyName] = "some",
            [IntegerPropertyName] = 123,
            [VectorPropertyName] = new ReadOnlyMemory<float>([10, 0, 0])
        };

        Assert.Null(await this.Collection.GetAsync(expectedKey));
        await this.Collection.UpsertAsync(inserted);

        var received = await this.Collection.GetAsync(expectedKey, new() { IncludeVectors = true });
        AssertEquivalent(inserted, received, includeVectors: true, fixture.TestStore.VectorsComparable);
    }

    [ConditionalFact]
    public virtual async Task Update_single_record()
    {
        var existingRecord = fixture.TestData[1];
        var updated = new Dictionary<string, object?>
        {
            [KeyPropertyName] = existingRecord[KeyPropertyName],
            [StringPropertyName] = "different",
            [IntegerPropertyName] = 456,
            [VectorPropertyName] = new ReadOnlyMemory<float>(Enumerable.Repeat(0.7f, 3).ToArray())
        };

        Assert.NotNull(await this.Collection.GetAsync((TKey)existingRecord[KeyPropertyName]!));
        await this.Collection.UpsertAsync(updated);

        var received = await this.Collection.GetAsync((TKey)existingRecord[KeyPropertyName]!, new() { IncludeVectors = true });
        AssertEquivalent(updated, received, includeVectors: true, fixture.TestStore.VectorsComparable);
    }

    [ConditionalFact]
    public virtual async Task Insert_multiple_records()
    {
        Dictionary<string, object?>[] newRecords =
        [
            new()
            {
                [KeyPropertyName] = fixture.GenerateNextKey<TKey>(),
                [IntegerPropertyName] = 100,
                [StringPropertyName] = "New record 1",
                [VectorPropertyName] = new ReadOnlyMemory<float>([10, 0, 1])
            },
            new()
            {
                [KeyPropertyName] = fixture.GenerateNextKey<TKey>(),
                [IntegerPropertyName] = 101,
                [StringPropertyName] = "New record 2",
                [VectorPropertyName] = new ReadOnlyMemory<float>([10, 0, 2])
            },
        ];

        var keys = newRecords.Select(record => record[KeyPropertyName]!).ToArray();
        Assert.Empty(await this.Collection.GetAsync(keys).ToArrayAsync());

        await this.Collection.UpsertAsync(newRecords);

        var received = await this.Collection.GetAsync(keys, new() { IncludeVectors = true }).ToArrayAsync();

        Assert.Collection(
            received.OrderBy(r => r[IntegerPropertyName]),
            r => AssertEquivalent(newRecords[0], r, includeVectors: true, fixture.TestStore.VectorsComparable),
            r => AssertEquivalent(newRecords[1], r, includeVectors: true, fixture.TestStore.VectorsComparable));
    }

    #endregion Upsert

    #region Delete

    [ConditionalFact]
    public async Task Delete_single_record()
    {
        var recordToRemove = fixture.TestData[2];

        Assert.NotNull(await fixture.Collection.GetAsync((TKey)recordToRemove[KeyPropertyName]!));
        await fixture.Collection.DeleteAsync((TKey)recordToRemove[KeyPropertyName]!);
        Assert.Null(await fixture.Collection.GetAsync((TKey)recordToRemove[KeyPropertyName]!));
    }

    // TODO: https://github.com/microsoft/semantic-kernel/issues/13303
    // [ConditionalFact]
    // public virtual async Task Delete_multiple_records()
    // {
    //     TKey[] keysToRemove = [(TKey)fixture.TestData[0][KeyPropertyName]!, (TKey)fixture.TestData[1][KeyPropertyName]!];

    //     await this.Collection.DeleteAsync(keysToRemove);
    //     Assert.Empty(await this.Collection.GetAsync(keysToRemove).ToArrayAsync());

    //     Assert.Equal(fixture.TestData.Count - 2, await this.GetRecordCount());
    // }

    [ConditionalFact]
    public virtual async Task DeleteAsync_does_nothing_for_non_existing_key()
    {
        TKey key = fixture.GenerateNextKey<TKey>();

        await fixture.Collection.DeleteAsync(key);
    }

    #endregion Delete

    #region Search

    [ConditionalTheory, MemberData(nameof(IncludeVectorsData))]
    public virtual async Task SearchAsync(bool includeVectors)
    {
        var expectedRecord = fixture.TestData[0];

        var result = await this.Collection
            .SearchAsync(
                expectedRecord[VectorPropertyName]!,
                top: 1,
                new() { IncludeVectors = includeVectors })
            .SingleAsync();

        AssertEquivalent(expectedRecord, result.Record, includeVectors, fixture.TestStore.VectorsComparable);
    }

    [ConditionalFact]
    public virtual async Task SearchAsync_with_Skip()
    {
        var result = await this.Collection
            .SearchAsync(
                fixture.TestData[0][VectorPropertyName]!,
                top: 1,
                new() { Skip = 1 })
            .SingleAsync();

        AssertEquivalent(fixture.TestData[1], result.Record, includeVectors: false, fixture.TestStore.VectorsComparable);
    }

    [ConditionalFact]
    public virtual async Task SearchAsync_with_Filter()
    {
        var result = await this.Collection
            .SearchAsync(
                fixture.TestData[0][VectorPropertyName]!,
                top: 1,
                new() { Filter = r => (int)r[IntegerPropertyName]! == 2 })
            .SingleAsync();

        AssertEquivalent(fixture.TestData[1], result.Record, includeVectors: false, fixture.TestStore.VectorsComparable);
    }

    #endregion Search

    protected static void AssertEquivalent(Dictionary<string, object?> expected, Dictionary<string, object?>? actual, bool includeVectors, bool compareVectors)
    {
        Assert.NotNull(actual);
        Assert.Equal(expected[KeyPropertyName], actual[KeyPropertyName]);

        Assert.Equal(expected[StringPropertyName], actual[StringPropertyName]);
        Assert.Equal(expected[IntegerPropertyName], actual[IntegerPropertyName]);

        if (includeVectors)
        {
            Assert.Equal(
                ((ReadOnlyMemory<float>)expected[VectorPropertyName]!).Length,
                ((ReadOnlyMemory<float>)actual[VectorPropertyName]!).Length);

            if (compareVectors)
            {
                Assert.Equal(
                    ((ReadOnlyMemory<float>)expected[VectorPropertyName]!).ToArray(),
                    ((ReadOnlyMemory<float>)actual[VectorPropertyName]!).ToArray());
            }
        }
        else
        {
            Assert.False(actual.ContainsKey(VectorPropertyName));
        }
    }

    public const string KeyPropertyName = "key";
    public const string StringPropertyName = "text";
    public const string IntegerPropertyName = "integer";
    public const string VectorPropertyName = "vector";

    protected VectorStoreCollection<object, Dictionary<string, object?>> Collection => fixture.Collection;

    public abstract class Fixture : DynamicVectorStoreCollectionFixture<TKey>
    {
        protected override string CollectionNameBase => nameof(DynamicModelTests<int>);

        protected override string KeyPropertyName => DynamicModelTests<TKey>.KeyPropertyName;

        protected override VectorStoreCollection<object, Dictionary<string, object?>> GetCollection()
            => this.TestStore.CreateDynamicCollection(this.CollectionName, this.CreateRecordDefinition());

        public override VectorStoreCollectionDefinition CreateRecordDefinition()
            => new()
            {
                Properties =
                [
                    new VectorStoreKeyProperty(this.KeyPropertyName, typeof(TKey)),
                    new VectorStoreDataProperty(StringPropertyName, typeof(string)) { IsIndexed = true},
                    new VectorStoreDataProperty(IntegerPropertyName, typeof(int)) { IsIndexed = true },
                    new VectorStoreVectorProperty(VectorPropertyName, typeof(ReadOnlyMemory<float>), dimensions: 3)
                    {
                        DistanceFunction = this.DistanceFunction,
                        IndexKind = this.IndexKind
                    }
                ]
            };

        protected override List<Dictionary<string, object?>> BuildTestData() =>
        [
            new()
            {
                [this.KeyPropertyName] = this.GenerateNextKey<TKey>(),
                [StringPropertyName] = "foo",
                [IntegerPropertyName] = 1,
                [VectorPropertyName] = new ReadOnlyMemory<float>([1, 2, 3])
            },
            new()
            {
                [this.KeyPropertyName] = this.GenerateNextKey<TKey>(),
                [StringPropertyName] = "bar",
                [IntegerPropertyName] = 2,
                [VectorPropertyName] = new ReadOnlyMemory<float>([1, 2, 4])
            },
            new()
            {
                [this.KeyPropertyName] = this.GenerateNextKey<TKey>(),
                [StringPropertyName] = "foo", // identical text as above
                [IntegerPropertyName] = 3,
                [VectorPropertyName] = new ReadOnlyMemory<float>([1, 2, 5])
            }
        ];
    }

    public Task InitializeAsync()
        => fixture.ReseedAsync();

    public Task DisposeAsync()
        => Task.CompletedTask;

    public static readonly TheoryData<bool> IncludeVectorsData = [false, true];
}
