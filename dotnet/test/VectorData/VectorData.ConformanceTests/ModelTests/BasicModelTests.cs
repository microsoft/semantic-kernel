// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace VectorData.ConformanceTests.ModelTests;

public abstract class BasicModelTests<TKey>(BasicModelTests<TKey>.Fixture fixture) : IAsyncLifetime
    where TKey : notnull
{
    #region Get

    [ConditionalTheory, MemberData(nameof(IncludeVectorsData))]
    public virtual async Task GetAsync_single_record(bool includeVectors)
    {
        var expectedRecord = fixture.TestData[0];

        var received = await this.Collection.GetAsync(expectedRecord.Key, new() { IncludeVectors = includeVectors });

        expectedRecord.AssertEqual(received, includeVectors, fixture.TestStore.VectorsComparable);
    }

    [ConditionalTheory, MemberData(nameof(IncludeVectorsData))]
    public virtual async Task GetAsync_multiple_records(bool includeVectors)
    {
        var expectedRecords = fixture.TestData.Take(2);
        var ids = expectedRecords.Select(record => record.Key);

        var received = await this.Collection.GetAsync(ids, new() { IncludeVectors = includeVectors }).ToArrayAsync();

        foreach (var record in expectedRecords)
        {
            record.AssertEqual(
                received.Single(r => r.Key.Equals(record.Key)),
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

        ArgumentNullException ex = await Assert.ThrowsAsync<ArgumentNullException>(() => this.Collection.GetAsync((TKey)default!));
        Assert.Equal("key", ex.ParamName);
    }

    [ConditionalFact]
    public virtual async Task GetAsync_throws_for_null_keys()
    {
        ArgumentNullException ex = await Assert.ThrowsAsync<ArgumentNullException>(() => this.Collection.GetAsync(keys: null!).ToArrayAsync().AsTask());
        Assert.Equal("keys", ex.ParamName);
    }

    [ConditionalFact]
    public virtual async Task GetAsync_returns_null_for_missing_key()
    {
        TKey key = fixture.GenerateNextKey<TKey>();

        Assert.Null(await this.Collection.GetAsync(key));
    }

    [ConditionalFact]
    public virtual async Task GetAsync_multiple_records_with_missing_keys_returns_only_existing()
    {
        var expectedRecords = fixture.TestData.Take(2).ToArray();
        var missingKey = fixture.GenerateNextKey<TKey>();
        var ids = expectedRecords.Select(record => record.Key).Append(missingKey).ToArray();

        var received = await this.Collection.GetAsync(ids).ToListAsync();

        Assert.Equal(2, received.Count);

        foreach (var record in expectedRecords)
        {
            record.AssertEqual(
                received.Single(r => r.Key.Equals(record.Key)),
                includeVectors: false,
                fixture.TestStore.VectorsComparable);
        }
    }

    [ConditionalFact]
    public virtual async Task GetAsync_returns_empty_for_empty_keys()
    {
        Assert.Empty(await this.Collection.GetAsync([]).ToArrayAsync());
    }

    [ConditionalTheory, MemberData(nameof(IncludeVectorsData))]
    public virtual async Task GetAsync_with_filter(bool includeVectors)
    {
        var expectedRecord = fixture.TestData[0];

        var results = await this.Collection.GetAsync(
            r => r.Number == 1,
            top: 2,
            new() { IncludeVectors = includeVectors })
            .ToListAsync();

        var receivedRecord = Assert.Single(results);
        expectedRecord.AssertEqual(receivedRecord, includeVectors, fixture.TestStore.VectorsComparable);
    }

    [ConditionalFact]
    public virtual async Task GetAsync_with_filter_by_true()
    {
        Assert.True(fixture.TestData.Count < 100);

        var count = await this.Collection.GetAsync(r => true, top: 100).CountAsync();

        Assert.Equal(fixture.TestData.Count, count);
    }

    [ConditionalFact]
    public virtual async Task GetAsync_with_filter_and_OrderBy()
    {
        var ascendingNumbers = fixture.TestData.Where(r => r.Number > 1).OrderBy(r => r.Number).Take(2).Select(r => r.Number).ToList();
        var descendingNumbers = fixture.TestData.Where(r => r.Number > 1).OrderByDescending(r => r.Number).Take(2).Select(r => r.Number).ToList();

        // Make sure the actual results are different for ascending/descending, otherwise the test is meaningless
        Assert.NotEqual(ascendingNumbers, descendingNumbers);

        var results = await this.Collection.GetAsync(
                r => r.Number > 1,
                top: 2,
                new() { OrderBy = o => o.Ascending(r => r.Number) })
            .Select(r => r.Number)
            .ToListAsync();

        Assert.Equal(ascendingNumbers, results);

        results = await this.Collection.GetAsync(
                r => r.Number > 1,
                top: 2,
                new() { OrderBy = o => o.Descending(r => r.Number) })
            .Select(r => r.Number)
            .ToListAsync();

        Assert.Equal(descendingNumbers, results);
    }

    [ConditionalFact]
    public virtual async Task GetAsync_with_filter_and_multiple_OrderBys()
    {
        var ascendingNumbers = fixture.TestData
            .OrderByDescending(r => r.Text)
            .ThenBy(r => r.Number)
            .Take(2).Select(r => r.Number).ToList();
        var descendingNumbers = fixture.TestData
            .OrderByDescending(r => r.Text)
            .ThenByDescending(r => r.Number)
            .Take(2)
            .Select(r => r.Number)
            .ToList();

        // Make sure the actual results are different for ascending/descending, otherwise the test is meaningless
        Assert.NotEqual(ascendingNumbers, descendingNumbers);

        var results = await this.Collection.GetAsync(
                r => true,
                top: 2,
                new() { OrderBy = o => o.Descending(r => r.Text).Ascending(r => r.Number) })
            .Select(r => r.Number)
            .ToListAsync();

        Assert.Equal(ascendingNumbers, results);

        results = await this.Collection.GetAsync(
                r => true,
                top: 2,
                new() { OrderBy = o => o.Descending(r => r.Text).Descending(r => r.Number) })
            .Select(r => r.Number)
            .ToListAsync();

        Assert.Equal(descendingNumbers, results);
    }

    [ConditionalFact]
    public virtual async Task GetAsync_with_filter_and_OrderBy_and_Skip()
    {
        var results = await this.Collection.GetAsync(
            r => r.Number > 1,
            top: 2,
            new() { OrderBy = o => o.Ascending(r => r.Number), Skip = 1 })
            .Select(r => r.Number)
            .ToListAsync();

        Assert.Equal(
            fixture.TestData.Where(r => r.Number > 1).OrderBy(r => r.Number).Skip(1).Take(2).Select(r => r.Number),
            results);
    }

    #endregion Get

    #region Upsert

    [ConditionalFact]
    public virtual async Task Insert_single_record()
    {
        TKey expectedKey = fixture.GenerateNextKey<TKey>();
        Record inserted = new()
        {
            Key = expectedKey,
            Text = "New record",
            Number = 123,
            Vector = new([10, 0, 0])
        };

        Assert.Null(await this.Collection.GetAsync(expectedKey));
        await this.Collection.UpsertAsync(inserted);

        var received = await this.Collection.GetAsync(expectedKey, new() { IncludeVectors = true });
        inserted.AssertEqual(received, includeVectors: true, fixture.TestStore.VectorsComparable);

        await fixture.TestStore.WaitForDataAsync(this.Collection, recordCount: fixture.TestData.Count + 1);
    }

    [ConditionalFact]
    public virtual async Task Update_single_record()
    {
        var existingRecord = fixture.TestData[1];
        Record updated = new()
        {
            Key = existingRecord.Key,
            Text = "Updated record",
            Number = 456,
            Vector = new([10, 0, 0])
        };

        Assert.NotNull(await this.Collection.GetAsync(existingRecord.Key));
        await this.Collection.UpsertAsync(updated);

        var received = await this.Collection.GetAsync(existingRecord.Key, new() { IncludeVectors = true });
        updated.AssertEqual(received, includeVectors: true, fixture.TestStore.VectorsComparable);
    }

    [ConditionalFact]
    public virtual async Task Insert_multiple_records()
    {
        Record[] newRecords =
        [
            new()
            {
                Key = fixture.GenerateNextKey<TKey>(),
                Number = 100,
                Text = "New record 1",
                Vector = new([10, 0, 1])
            },
            new()
            {
                Key = fixture.GenerateNextKey<TKey>(),
                Number = 101,
                Text = "New record 2",
                Vector = new([10, 0, 2])
            },
        ];

        var keys = newRecords.Select(record => record.Key).ToArray();
        Assert.Empty(await this.Collection.GetAsync(keys).ToArrayAsync());

        await this.Collection.UpsertAsync(newRecords);

        var received = await this.Collection.GetAsync(keys, new() { IncludeVectors = true }).ToArrayAsync();

        Assert.Collection(
            received.OrderBy(r => r.Number),
            r => newRecords[0].AssertEqual(r, includeVectors: true, fixture.TestStore.VectorsComparable),
            r => newRecords[1].AssertEqual(r, includeVectors: true, fixture.TestStore.VectorsComparable));
    }

    [ConditionalFact]
    public virtual async Task Update_multiple_records()
    {
        Record[] existingRecords =
        [
            new()
            {
                Key = fixture.TestData[0].Key,
                Number = 101,
                Text = "Updated record 1",
                Vector = new([10, 0, 1])
            },
            new()
            {
                Key = fixture.TestData[1].Key,
                Number = 102,
                Text = "Updated record 2",
                Vector = new([10, 0, 2])
            }
        ];

        await this.Collection.UpsertAsync(existingRecords);

        var keys = existingRecords.Select(record => record.Key).ToArray();
        var received = await this.Collection.GetAsync(keys, new() { IncludeVectors = true }).ToArrayAsync();

        Assert.Collection(
            received.OrderBy(r => r.Number),
            r => existingRecords[0].AssertEqual(r, includeVectors: true, fixture.TestStore.VectorsComparable),
            r => existingRecords[1].AssertEqual(r, includeVectors: true, fixture.TestStore.VectorsComparable));
    }

    [ConditionalFact]
    public virtual async Task Insert_and_update_in_same_batch()
    {
        Record[] records =
        [
            new()
            {
                Key = fixture.GenerateNextKey<TKey>(),
                Number = 101,
                Text = "New record",
                Vector = new([10, 0, 1])
            },
            new()
            {
                Key = fixture.TestData[0].Key,
                Number = 102,
                Text = "Updated record",
                Vector = new([10, 0, 2])
            },
        ];

        await this.Collection.UpsertAsync(records);

        var keys = records.Select(record => record.Key).ToArray();
        var received = await this.Collection.GetAsync(keys, new() { IncludeVectors = true }).ToArrayAsync();

        Assert.Collection(
            received.OrderBy(r => r.Number),
            r => records[0].AssertEqual(r, includeVectors: true, fixture.TestStore.VectorsComparable),
            r => records[1].AssertEqual(r, includeVectors: true, fixture.TestStore.VectorsComparable));
    }

    [ConditionalFact]
    public virtual async Task UpsertAsync_throws_for_null_batch()
    {
        ArgumentNullException ex = await Assert.ThrowsAsync<ArgumentNullException>(() => this.Collection.UpsertAsync(records: null!));
        Assert.Equal("records", ex.ParamName);
    }

    [ConditionalFact]
    public virtual async Task UpsertAsync_does_nothing_for_empty_batch()
    {
        Assert.True(fixture.TestData.Count < 100);

        var beforeCount = await this.Collection.GetAsync(r => true, top: 100).CountAsync();
        await this.Collection.UpsertAsync([]);
        var afterCount = await this.Collection.GetAsync(r => true, top: 100).CountAsync();

        Assert.Equal(afterCount, beforeCount);
    }

    #endregion Upsert

    #region Delete

    [ConditionalFact]
    public virtual async Task Delete_single_record()
    {
        var keyToRemove = fixture.TestData[0].Key;

        await this.Collection.DeleteAsync(keyToRemove);
        Assert.Null(await this.Collection.GetAsync(keyToRemove));
    }

    [ConditionalFact]
    public virtual async Task Delete_multiple_records()
    {
        TKey[] keysToRemove = [fixture.TestData[0].Key, fixture.TestData[1].Key];

        await this.Collection.DeleteAsync(keysToRemove);
        Assert.Empty(await this.Collection.GetAsync(keysToRemove).ToArrayAsync());
    }

    [ConditionalFact]
    public virtual async Task DeleteAsync_does_nothing_for_non_existing_key()
    {
        var beforeCount = await this.Collection.GetAsync(r => true, top: 100).CountAsync();
        await this.Collection.DeleteAsync(fixture.GenerateNextKey<TKey>());
        var afterCount = await this.Collection.GetAsync(r => true, top: 100).CountAsync();

        Assert.Equal(afterCount, beforeCount);
    }

    [ConditionalFact]
    public virtual async Task DeleteAsync_does_nothing_for_empty_batch()
    {
        var beforeCount = await this.Collection.GetAsync(r => true, top: 100).CountAsync();
        await this.Collection.DeleteAsync([]);
        var afterCount = await this.Collection.GetAsync(r => true, top: 100).CountAsync();

        Assert.Equal(afterCount, beforeCount);
    }

    [ConditionalFact]
    public virtual async Task DeleteAsync_throws_for_null_keys()
    {
        ArgumentNullException ex = await Assert.ThrowsAsync<ArgumentNullException>(() => this.Collection.DeleteAsync(keys: null!));
        Assert.Equal("keys", ex.ParamName);
    }

    #endregion Delete

    #region Search

    [ConditionalTheory, MemberData(nameof(IncludeVectorsData))]
    public virtual async Task SearchAsync(bool includeVectors)
    {
        var expectedRecord = fixture.TestData[0];

        var result = await this.Collection
            .SearchAsync(
                expectedRecord.Vector,
                top: 1,
                new() { IncludeVectors = includeVectors })
            .SingleAsync();

        expectedRecord.AssertEqual(result.Record, includeVectors, fixture.TestStore.VectorsComparable);
    }

    [ConditionalFact]
    public virtual async Task SearchAsync_with_Skip()
    {
        var result = await this.Collection
            .SearchAsync(
                fixture.TestData[0].Vector,
                top: 1,
                new() { Skip = 1 })
            .SingleAsync();

        fixture.TestData[1].AssertEqual(result.Record, includeVectors: false, fixture.TestStore.VectorsComparable);
    }

    [ConditionalFact]
    public virtual async Task SearchAsync_with_Filter()
    {
        var result = await this.Collection
            .SearchAsync(
                fixture.TestData[0].Vector,
                top: 1,
                new() { Filter = r => r.Number == 2 })
            .SingleAsync();

        fixture.TestData[1].AssertEqual(result.Record, includeVectors: false, fixture.TestStore.VectorsComparable);
    }

    #endregion Search

    protected VectorStoreCollection<TKey, Record> Collection => fixture.Collection;

    public abstract class Fixture : VectorStoreCollectionFixture<TKey, Record>
    {
        protected override string CollectionNameBase => nameof(BasicModelTests<int>);

        protected override List<Record> BuildTestData() =>
        [
            new()
            {
                Key = this.GenerateNextKey<TKey>(),
                Number = 1,
                Text = "foo",
                Vector = new([1, 2, 3])
            },
            new()
            {
                Key = this.GenerateNextKey<TKey>(),
                Number = 2,
                Text = "bar",
                Vector = new([1, 2, 4])
            },
            new()
            {
                Key = this.GenerateNextKey<TKey>(),
                Number = 3,
                Text = "foo", // identical text as above
                Vector = new([1, 2, 5])
            }
        ];

        public override VectorStoreCollectionDefinition CreateRecordDefinition()
            => new()
            {
                Properties =
                [
                    new VectorStoreKeyProperty(nameof(Record.Key), typeof(TKey)),
                    new VectorStoreVectorProperty(nameof(Record.Vector), typeof(ReadOnlyMemory<float>), 3)
                    {
                        DistanceFunction = this.DistanceFunction,
                        IndexKind = this.IndexKind
                    },

                    new VectorStoreDataProperty(nameof(Record.Number), typeof(int)) { IsIndexed = true },
                    new VectorStoreDataProperty(nameof(Record.Text), typeof(string)) { IsIndexed = true },
                ]
            };
    }

    public sealed class Record : TestRecord<TKey>
    {
        [VectorStoreData(StorageName = "text")]
        public string? Text { get; set; }

        [VectorStoreData(StorageName = "number")]
        public int Number { get; set; }

        [VectorStoreVector(Dimensions: 3, StorageName = "vector")]
        public ReadOnlyMemory<float> Vector { get; set; }

        public void AssertEqual(Record? other, bool includeVectors, bool compareVectors)
        {
            Assert.NotNull(other);
            Assert.Equal(this.Key, other.Key);
            Assert.Equal(this.Text, other.Text);
            Assert.Equal(this.Number, other.Number);

            if (includeVectors)
            {
                Assert.Equal(this.Vector.Span.Length, other.Vector.Span.Length);

                if (compareVectors)
                {
                    Assert.Equal(this.Vector.ToArray(), other.Vector.ToArray());
                }
            }
            else
            {
                Assert.Equal(0, other.Vector.Length);
            }
        }

        public override string ToString()
            => $"Key: {this.Key}, Text: {this.Text}";
    }

    public Task InitializeAsync()
        => fixture.ReseedAsync();

    public Task DisposeAsync()
        => Task.CompletedTask;

    public static readonly TheoryData<bool> IncludeVectorsData = [false, true];
}
