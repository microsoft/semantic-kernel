// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
#pragma warning disable CA2000 // Dispose objects before losing scope

namespace VectorDataSpecificationTests;

/// <summary>
/// Tests that the various embedding types natively supported by the provider (<c>ReadOnlyMemory&lt;float&gt;</c>, <c>ReadOnlyMemory&lt;Half&gt;</c>...) work correctly.
/// </summary>
public abstract class EmbeddingTypeTests<TKey>(EmbeddingTypeTests<TKey>.Fixture fixture)
    where TKey : notnull
{
    [ConditionalFact]
    public virtual Task ReadOnlyMemory_of_float()
        => this.Test<ReadOnlyMemory<float>>(
            new ReadOnlyMemory<float>([1, 2, 3]),
            new ReadOnlyMemoryEmbeddingGenerator<float>(new([1, 2, 3])));

    protected virtual async Task Test<TVector>(TVector value, IEmbeddingGenerator? embeddingGenerator = null, string? distanceFunction = null, int dimensions = 3)
        where TVector : notnull
    {
        var collection = fixture.VectorStore.GetCollection<TKey, Record<TVector>>(fixture.CollectionName, fixture.CreateRecordDefinition<TVector>(embeddingGenerator: null, distanceFunction, dimensions));

        await collection.DeleteCollectionAsync();
        await collection.EnsureCollectionExistsAsync();

        var key = fixture.GenerateNextKey<TKey>();
        var record = new Record<TVector>
        {
            Key = key,
            Vector = value,
            Int = 42
        };

        await collection.UpsertAsync(record);

        await fixture.TestStore.WaitForDataAsync(collection, recordCount: 1, dummyVector: value);

        var result1 = await collection.GetAsync(key, new() { IncludeVectors = true });
        Assert.Equal(42, result1!.Int);

        var result2 = await collection.SearchEmbeddingAsync(value, top: 1, new() { IncludeVectors = true }).SingleAsync();
        Assert.Equal(42, result2.Record.Int);

        // Test embedding generation
        if (embeddingGenerator is not null)
        {
            if (fixture.RecreateCollection)
            {
                await collection.DeleteCollectionAsync();
            }
            else
            {
                await collection.DeleteAsync(key);
            }

            var collection2 = fixture.VectorStore.GetCollection<TKey, RecordWithString>(fixture.CollectionName, fixture.CreateRecordDefinition<string>(embeddingGenerator, distanceFunction, dimensions));

            if (fixture.RecreateCollection)
            {
                await collection2.EnsureCollectionExistsAsync();
            }

            var key2 = fixture.GenerateNextKey<TKey>();
            var record2 = new RecordWithString
            {
                Key = key,
                Vector = "does not matter",
                Int = 43
            };

            await collection2.UpsertAsync(record2);

            await fixture.TestStore.WaitForDataAsync(collection2, recordCount: 1, dummyVector: value);

            var result3 = await collection2.GetAsync(key);
            Assert.Equal(43, result3!.Int);

            var result4 = await collection2.SearchAsync("does not matter", top: 1).SingleAsync();
            Assert.Equal(43, result4.Record.Int);
        }
    }

    protected sealed class ReadOnlyMemoryEmbeddingGenerator<T>(ReadOnlyMemory<T> data) : IEmbeddingGenerator<string, Embedding<T>>
    {
        public Task<GeneratedEmbeddings<Embedding<T>>> GenerateAsync(IEnumerable<string> values, EmbeddingGenerationOptions? options = null, CancellationToken cancellationToken = default)
            => Task.FromResult(new GeneratedEmbeddings<Embedding<T>>([new(data)]));

        public object? GetService(Type serviceType, object? serviceKey = null) => null;
        public void Dispose() { }
    }

    public class RecordWithString
    {
        public TKey Key { get; set; }
        public string Vector { get; set; }
        public int Int { get; set; }
    }

    public class Record<TVector>
    {
        public TKey Key { get; set; }
        public TVector Vector { get; set; }
        public int Int { get; set; }
    }

    public abstract class Fixture : VectorStoreFixture
    {
        public virtual string CollectionName => "EmbeddingTypeTests";

        public virtual VectorStoreRecordDefinition CreateRecordDefinition<TVectorProperty>(IEmbeddingGenerator? embeddingGenerator, string? distanceFunction, int dimensions)
            => new()
            {
                Properties =
                [
                    new VectorStoreKeyProperty("Key", typeof(TKey)),
                    new VectorStoreVectorProperty("Vector", typeof(TVectorProperty), dimensions)
                    {
                        DistanceFunction = distanceFunction ?? this.DefaultDistanceFunction,
                        IndexKind = this.DefaultIndexKind
                    },
                    new VectorStoreDataProperty("Int", typeof(int))
                ],
                EmbeddingGenerator = embeddingGenerator
            };

        public virtual bool RecreateCollection => false;
    }
}
