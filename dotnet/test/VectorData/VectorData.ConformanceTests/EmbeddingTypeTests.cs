// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
#pragma warning disable CA2000 // Dispose objects before losing scope

namespace VectorData.ConformanceTests;

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
            new ReadOnlyMemoryEmbeddingGenerator<float>([1, 2, 3]),
            vectorEqualityAsserter: (e, a) => Assert.Equal(e.Span.ToArray(), a.Span.ToArray()));

    [ConditionalFact]
    public virtual Task Embedding_of_float()
        => this.Test<Embedding<float>>(
            new Embedding<float>(new ReadOnlyMemory<float>([1, 2, 3])),
            new ReadOnlyMemoryEmbeddingGenerator<float>([1, 2, 3]),
            vectorEqualityAsserter: (e, a) => Assert.Equal(e.Vector.Span.ToArray(), a.Vector.Span.ToArray()));

    [ConditionalFact]
    public virtual Task Array_of_float()
        => this.Test<float[]>(
            [1, 2, 3],
            new ReadOnlyMemoryEmbeddingGenerator<float>([1, 2, 3]));

    protected virtual async Task Test<TVector>(TVector value, IEmbeddingGenerator? embeddingGenerator = null, Action<TVector, TVector>? vectorEqualityAsserter = null, string? distanceFunction = null, int dimensions = 3)
        where TVector : notnull
    {
        vectorEqualityAsserter ??= (e, a) => Assert.Equal(e, a);

        await fixture.VectorStore.EnsureCollectionDeletedAsync(fixture.CollectionName);

        var collection = fixture.VectorStore.GetCollection<TKey, Record<TVector>>(fixture.CollectionName, fixture.CreateRecordDefinition<TVector>(embeddingGenerator: null, distanceFunction, dimensions));
        await collection.EnsureCollectionExistsAsync();

        var key = fixture.GenerateNextKey<TKey>();
        var record = new Record<TVector>
        {
            Key = key,
            Vector = value,
            Int = 42
        };

        await collection.UpsertAsync(record);

        await fixture.TestStore.WaitForDataAsync(collection, recordCount: 1, filter: r => r.Int == 42, dummyVector: value);

        var result1 = await collection.GetAsync(key, new() { IncludeVectors = true });
        Assert.Equal(42, result1!.Int);
        if (fixture.TestStore.VectorsComparable)
        {
            vectorEqualityAsserter(value, result1.Vector);
        }

        // Note that some databases leak indexing information across deletion/recreation of the same collection name (e.g. Pinecone) - so we also
        // filter by Int here.
        var result2 = await collection.SearchAsync(value, top: 1, new() { IncludeVectors = true, Filter = r => r.Int == 42 }).SingleAsync();
        Assert.Equal(42, result2.Record.Int);
        if (fixture.TestStore.VectorsComparable)
        {
            vectorEqualityAsserter(value, result2.Record.Vector);
        }

        ///////////////////////
        // Test dynamic mapping
        ///////////////////////
        if (fixture.RecreateCollection)
        {
            await collection.EnsureCollectionDeletedAsync();
        }
        else
        {
            await collection.DeleteAsync(key);
        }

        var dynamicCollection = fixture.VectorStore.GetDynamicCollection(fixture.CollectionName, fixture.CreateRecordDefinition<TVector>(embeddingGenerator, distanceFunction, dimensions));

        if (fixture.RecreateCollection)
        {
            await dynamicCollection.EnsureCollectionExistsAsync();
        }

        key = fixture.GenerateNextKey<TKey>();
        var dynamicRecord = new Dictionary<string, object?>
        {
            ["Key"] = key,
            ["Vector"] = value,
            ["Int"] = 43
        };

        await dynamicCollection.UpsertAsync(dynamicRecord);

        await fixture.TestStore.WaitForDataAsync(dynamicCollection, recordCount: 1, filter: r => (int)r["Int"]! == 43, dummyVector: value);

        var dynamicResult1 = await dynamicCollection.GetAsync(key, new() { IncludeVectors = true });
        Assert.Equal(43, dynamicResult1!["Int"]);
        if (fixture.TestStore.VectorsComparable)
        {
            vectorEqualityAsserter(value, (TVector)dynamicResult1["Vector"]!);
        }

        // Note that some databases leak indexing information across deletion/recreation of the same collection name (e.g. Pinecone) - so we also
        // filter by Int here.
        var dynamicResult2 = await dynamicCollection.SearchAsync(value, top: 1, new() { IncludeVectors = true, Filter = r => (int)r["Int"]! == 43 }).SingleAsync();
        Assert.Equal(43, dynamicResult2.Record["Int"]);
        if (fixture.TestStore.VectorsComparable)
        {
            vectorEqualityAsserter(value, (TVector)dynamicResult2.Record["Vector"]!);
        }

        ////////////////////////////
        // Test embedding generation
        ////////////////////////////
        if (embeddingGenerator is not null)
        {
            if (fixture.RecreateCollection)
            {
                await collection.EnsureCollectionDeletedAsync();
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
                Int = 44
            };

            await collection2.UpsertAsync(record2);

            await fixture.TestStore.WaitForDataAsync(collection2, recordCount: 1, filter: r => r.Int == 44, dummyVector: value);

            var result3 = await collection2.GetAsync(key);
            Assert.Equal(44, result3!.Int);
            if (fixture.AssertNoVectorsLoadedWithEmbeddingGeneration)
            {
                Assert.Null(result3.Vector);
            }

            var result4 = await collection2.SearchAsync("does not matter", top: 1, new() { Filter = r => r.Int == 44 }).SingleAsync();
            Assert.Equal(44, result4.Record.Int);
            if (fixture.AssertNoVectorsLoadedWithEmbeddingGeneration)
            {
                Assert.Null(result4.Record.Vector);
            }
        }
    }

    protected sealed class ReadOnlyMemoryEmbeddingGenerator<T>(T[] data) : IEmbeddingGenerator<string, Embedding<T>>
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

        public virtual VectorStoreCollectionDefinition CreateRecordDefinition<TVectorProperty>(IEmbeddingGenerator? embeddingGenerator, string? distanceFunction, int dimensions)
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
                    new VectorStoreDataProperty("Int", typeof(int)) { IsIndexed = true }
                ],
                EmbeddingGenerator = embeddingGenerator
            };

        /// <summary>
        /// Whether the recreate the collection while testing, as opposed to deleting the records.
        /// Necessary for InMemory, where the .NET mapped on the collection cannot be changed.
        /// </summary>
        public virtual bool RecreateCollection => false;

        /// <summary>
        /// Whether to assert that no vectors were loaded when embedding generation is used.
        /// Necessary for InMemory which returns the same object which was inserted, and therefore contains
        /// the original input value.
        /// </summary>
        public virtual bool AssertNoVectorsLoadedWithEmbeddingGeneration => true;
    }
}
