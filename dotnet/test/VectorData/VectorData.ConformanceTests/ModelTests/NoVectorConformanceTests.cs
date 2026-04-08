// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace VectorData.ConformanceTests.ModelTests;

/// <summary>
/// Tests operations using a model without a vector.
/// This is only supported by a subset of databases so only extend if applicable for your database.
/// </summary>
public class NoVectorModelTests<TKey>(NoVectorModelTests<TKey>.Fixture fixture) : IAsyncLifetime
    where TKey : notnull
{
    [ConditionalTheory, MemberData(nameof(IncludeVectorsData))]
    public virtual async Task GetAsync_single_record(bool includeVectors)
    {
        var expectedRecord = fixture.TestData[0];

        var received = await this.Collection.GetAsync(expectedRecord.Key, new() { IncludeVectors = includeVectors });

        expectedRecord.AssertEqual(received);
    }

    [ConditionalFact]
    public virtual async Task Insert_single_record()
    {
        TKey expectedKey = fixture.GenerateNextKey<TKey>();
        NoVectorRecord inserted = new()
        {
            Key = expectedKey,
            Text = "New record"
        };

        Assert.Null(await this.Collection.GetAsync(expectedKey));
        await this.Collection.UpsertAsync(inserted);

        var received = await this.Collection.GetAsync(expectedKey, new() { IncludeVectors = true });
        inserted.AssertEqual(received);
    }

    [ConditionalFact]
    public virtual async Task Delete_single_record()
    {
        var keyToRemove = fixture.TestData[0].Key;

        await this.Collection.DeleteAsync(keyToRemove);
        Assert.Null(await this.Collection.GetAsync(keyToRemove));
    }

    protected VectorStoreCollection<TKey, NoVectorRecord> Collection => fixture.Collection;

    public abstract class Fixture : VectorStoreCollectionFixture<TKey, NoVectorRecord>
    {
        protected override string CollectionNameBase => nameof(NoVectorModelTests<int>);

        protected override List<NoVectorRecord> BuildTestData() =>
        [
            new()
            {
                Key = this.GenerateNextKey<TKey>(),
                Text = "foo",
            },
            new()
            {
                Key = this.GenerateNextKey<TKey>(),
                Text = "bar",
            }
        ];

        public override VectorStoreCollectionDefinition CreateRecordDefinition()
            => new()
            {
                Properties =
                [
                    new VectorStoreKeyProperty(nameof(NoVectorRecord.Key), typeof(TKey)),
                    new VectorStoreDataProperty(nameof(NoVectorRecord.Text), typeof(string)) { IsIndexed = true }
                ]
            };

        // The default implementation of WaitForDataAsync uses SearchAsync, but our model has no vectors.
        protected override async Task WaitForDataAsync()
        {
            for (var i = 0; i < 200; i++)
            {
                var results = await this.Collection.GetAsync([this.TestData[0].Key, this.TestData[1].Key]).ToArrayAsync();
                if (results.Length == this.TestData.Count && results.All(r => r != null))
                {
                    return;
                }

                await Task.Delay(TimeSpan.FromMilliseconds(100));
            }

            throw new InvalidOperationException("Data did not appear in the collection within the expected time.");
        }
    }

    public sealed class NoVectorRecord : TestRecord<TKey>
    {
        [VectorStoreData(StorageName = "text")]
        public string? Text { get; set; }

        public void AssertEqual(NoVectorRecord? other)
        {
            Assert.NotNull(other);
            Assert.Equal(this.Key, other.Key);
            Assert.Equal(this.Text, other.Text);
        }
    }

    public Task InitializeAsync()
        => fixture.ReseedAsync();

    public Task DisposeAsync()
        => Task.CompletedTask;

    public static readonly TheoryData<bool> IncludeVectorsData = [false, true];
}
