// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace VectorData.ConformanceTests.ModelTests;

/// <summary>
/// Tests using a model without data fields, only a key and an embedding.
/// </summary>
public class NoDataModelTests<TKey>(NoDataModelTests<TKey>.Fixture fixture) : IAsyncLifetime
    where TKey : notnull
{
    [ConditionalTheory, MemberData(nameof(IncludeVectorsData))]
    public virtual async Task GetAsync_single_record(bool includeVectors)
    {
        var expectedRecord = fixture.TestData[0];

        var received = await this.Collection.GetAsync(expectedRecord.Key, new() { IncludeVectors = includeVectors });

        expectedRecord.AssertEqual(received, includeVectors, fixture.TestStore.VectorsComparable);
    }

    [ConditionalFact]
    public virtual async Task Insert_single_record()
    {
        TKey expectedKey = fixture.GenerateNextKey<TKey>();
        NoDataRecord inserted = new()
        {
            Key = expectedKey,
            Floats = new([10, 0, 0])
        };

        Assert.Null(await this.Collection.GetAsync(expectedKey));
        await this.Collection.UpsertAsync(inserted);

        var received = await this.Collection.GetAsync(expectedKey, new() { IncludeVectors = true });
        inserted.AssertEqual(received, includeVectors: true, fixture.TestStore.VectorsComparable);
    }

    [ConditionalFact]
    public virtual async Task Delete_single_record()
    {
        var keyToRemove = fixture.TestData[0].Key;

        await this.Collection.DeleteAsync(keyToRemove);
        Assert.Null(await this.Collection.GetAsync(keyToRemove));
    }

    protected VectorStoreCollection<TKey, NoDataRecord> Collection => fixture.Collection;

    public abstract class Fixture : VectorStoreCollectionFixture<TKey, NoDataRecord>
    {
        public override string CollectionName => "NoDataModelTests";

        protected override List<NoDataRecord> BuildTestData() =>
        [
            new()
            {
                Key = this.GenerateNextKey<TKey>(),
                Floats = new([1, 2, 3])
            },
            new()
            {
                Key = this.GenerateNextKey<TKey>(),
                Floats = new([1, 2, 4])
            }
        ];

        public override VectorStoreCollectionDefinition CreateRecordDefinition()
            => new()
            {
                Properties =
                [
                    new VectorStoreKeyProperty(nameof(NoDataRecord.Key), typeof(TKey)),
                    new VectorStoreVectorProperty(nameof(NoDataRecord.Floats), typeof(ReadOnlyMemory<float>), 3)
                    {
                        IndexKind = this.IndexKind
                    }
                ]
            };
    }

    public sealed class NoDataRecord : TestRecord<TKey>
    {
        [VectorStoreVector(Dimensions: 3, StorageName = "embedding")]
        public ReadOnlyMemory<float> Floats { get; set; }

        public void AssertEqual(NoDataRecord? other, bool includeVectors, bool compareVectors)
        {
            Assert.NotNull(other);
            Assert.Equal(this.Key, other.Key);

            if (includeVectors)
            {
                Assert.Equal(this.Floats.Span.Length, other.Floats.Span.Length);

                if (compareVectors)
                {
                    Assert.True(this.Floats.Span.SequenceEqual(other.Floats.Span));
                }
            }
        }
    }

    public Task InitializeAsync()
        => fixture.ReseedAsync();

    public Task DisposeAsync()
        => Task.CompletedTask;

    public static readonly TheoryData<bool> IncludeVectorsData = [false, true];
}
