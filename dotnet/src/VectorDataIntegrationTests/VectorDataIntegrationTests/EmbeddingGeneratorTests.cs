// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Support;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.Properties;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests;

public abstract class EmbeddingGeneratorTests<TKey>(EmbeddingGeneratorTests<TKey>.Fixture fixture)
    where TKey : notnull
{
    [ConditionalFact]
    public virtual async Task Property_generator_is_used()
    {
        var results = await fixture.CollectionWithPropertyGenerator.SearchAsync("foo", new() { Top = 1 })
            .ConfigureAwait(false);
        var record = (await results.Results.SingleAsync()).Record;
        Assert.Equal("Property ([1, 1, 3])", record.Text);
    }

    [ConditionalFact]
    public virtual async Task Collection_generator_is_used()
    {
        var results = await fixture.CollectionWithCollectionGenerator.SearchAsync("foo", new() { Top = 1 })
            .ConfigureAwait(false);
        var record = (await results.Results.SingleAsync()).Record;
        Assert.Equal("Collection ([1, 1, 2])", record.Text);
    }

    [ConditionalFact]
    public virtual async Task Store_generator_is_used()
    {
        var results = await fixture.CollectionWithStoreGenerator.SearchAsync("foo", new() { Top = 1 })
            .ConfigureAwait(false);
        var record = (await results.Results.SingleAsync()).Record;
        Assert.Equal("Store ([1, 1, 1])", record.Text);
    }

    [ConditionalFact]
    public virtual async Task No_configured_generator_throws()
    {
        // CollectionWithNoGenerator has no generator configured at any level, so SearchAsync
        // should throw.
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            fixture.CollectionWithNoGenerator.SearchAsync("foo", new() { Top = 1 }));

        Assert.Equal(VectorDataStrings.NoEmbeddingGeneratorWasConfigured, exception.Message);
    }

    [ConditionalFact]
    public virtual async Task Incompatible_generator_throws()
    {
        // We have a generator configured for string, not int.
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            fixture.CollectionWithStoreGenerator.SearchAsync(8, new() { Top = 1 }));

        Assert.Equal(string.Format(VectorDataStrings.IncompatibleEmbeddingGeneratorWasConfigured, nameof(Int32), nameof(FakeEmbeddingGenerator)), exception.Message);
    }

    // TODO: Upsert tests

    public class EmbeddingGeneratorRecord
    {
        public TKey Key { get; set; } = default!;
        public ReadOnlyMemory<float>? Vector { get; set; }

        public string? Text { get; set; }
    }

    public abstract class Fixture : VectorStoreCollectionFixture<TKey, EmbeddingGeneratorRecord>
    {
        protected override string CollectionName => "EmbeddingGeneratorTests";

        protected override VectorStoreRecordDefinition GetRecordDefinition()
            => new()
            {
                Properties =
                [
                    new VectorStoreRecordKeyProperty(nameof(EmbeddingGeneratorRecord.Key), typeof(TKey)),
                    new VectorStoreRecordVectorProperty(nameof(EmbeddingGeneratorRecord.Vector), typeof(ReadOnlyMemory<float>?))
                    {
                        Dimensions = 3,
                        DistanceFunction = this.DefaultDistanceFunction,
                        IndexKind = this.DefaultIndexKind
                    },

                    new VectorStoreRecordDataProperty(nameof(EmbeddingGeneratorRecord.Text), typeof(string))
                ]
            };

        protected override List<EmbeddingGeneratorRecord> BuildTestData() =>
        [
            new()
            {
                Key = this.GenerateNextKey<TKey>(),
                Vector = new ReadOnlyMemory<float>([1, 1, 1]),
                Text = "Store ([1, 1, 1])"
            },
            new()
            {
                Key = this.GenerateNextKey<TKey>(),
                Vector = new ReadOnlyMemory<float>([1, 1, 2]),
                Text = "Collection ([1, 1, 2])"
            },
            new()
            {
                Key = this.GenerateNextKey<TKey>(),
                Vector = new ReadOnlyMemory<float>([1, 1, 3]),
                Text = "Property ([1, 1, 3])"
            }
        ];

        public virtual IVectorStoreRecordCollection<TKey, EmbeddingGeneratorRecord> CollectionWithPropertyGenerator { get; private set; } = null!;
        public virtual IVectorStoreRecordCollection<TKey, EmbeddingGeneratorRecord> CollectionWithCollectionGenerator { get; private set; } = null!;
        public virtual IVectorStoreRecordCollection<TKey, EmbeddingGeneratorRecord> CollectionWithStoreGenerator { get; private set; } = null!;
        public virtual IVectorStoreRecordCollection<TKey, EmbeddingGeneratorRecord> CollectionWithNoGenerator => this.Collection;

        // TODO: DI

        protected virtual IVectorStoreRecordCollection<TKey, EmbeddingGeneratorRecord> CreateCollection(
            IVectorStore vectorStore,
            string collectionName,
            VectorStoreRecordDefinition recordDefinition)
            => vectorStore.GetCollection<TKey, EmbeddingGeneratorRecord>(collectionName, recordDefinition);

        // TODO: Change type from object? to non-generic IEmbeddingGenerator once MEAI is updated.
        protected abstract IVectorStore CreateVectorStore(object? embeddingGenerator);

#pragma warning disable CA2000 // Call Dispose on FakeEmbeddingGenerator
        public override async Task InitializeAsync()
        {
            await base.InitializeAsync();

            // The base fixture has created the collection in the database, and we have Collection without any
            // embedding generators.
            // Create extra IVectorStoreRecordCollection instances with different embedding generator configurations.
            var recordDefinition = this.GetRecordDefinition();
            var storeWithEmbeddingGenerator = this.CreateVectorStore(new FakeEmbeddingGenerator([1, 1, 1]));

            // Embedding generators are defined at all level - the property one should take precedence
            this.CollectionWithPropertyGenerator = this.CreateCollection(
                storeWithEmbeddingGenerator,
                this.CollectionName,
                new()
                {
                    EmbeddingGenerator = new FakeEmbeddingGenerator([1, 1, 2]),
                    Properties = recordDefinition.Properties
                        .Select(p => p is VectorStoreRecordVectorProperty vectorProperty
                            ? new VectorStoreRecordVectorProperty(vectorProperty) { EmbeddingGenerator = new FakeEmbeddingGenerator([1, 1, 3]) }
                            : p)
                        .ToList()
                });

            // Embedding generators are defined at the collection and store level - the store one should take precedence
            this.CollectionWithCollectionGenerator = this.CreateCollection(
                storeWithEmbeddingGenerator,
                this.CollectionName,
                new()
                {
                    EmbeddingGenerator = new FakeEmbeddingGenerator([1, 1, 2]),
                    Properties = recordDefinition.Properties
                });

            // An embedding generator are defined at the store level only
            this.CollectionWithStoreGenerator = this.CreateCollection(
                storeWithEmbeddingGenerator,
                this.CollectionName,
                recordDefinition);
        }
#pragma warning restore CA2000 // Call Dispose on FakeEmbeddingGenerator
    }

    private sealed class FakeEmbeddingGenerator(float[] embeddingToReturn) : IEmbeddingGenerator<string, Embedding<float>>
    {
        public Task<GeneratedEmbeddings<Embedding<float>>> GenerateAsync(
            IEnumerable<string> values,
            EmbeddingGenerationOptions? options = null,
            CancellationToken cancellationToken = default)
        {
            var results = new GeneratedEmbeddings<Embedding<float>>();

            var count = values.Count();

            for (var i = 0; i < count; i++)
            {
                results.Add(new Embedding<float>(new ReadOnlyMemory<float>(embeddingToReturn)));
            }

            return Task.FromResult(results);
        }

        public object? GetService(Type serviceType, object? serviceKey = null)
            => null;

        public void Dispose() {}
    }
}
