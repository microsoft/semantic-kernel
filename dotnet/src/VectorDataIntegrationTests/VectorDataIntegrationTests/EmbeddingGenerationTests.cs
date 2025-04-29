// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.Properties;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests;

#pragma warning disable CA1819 // Properties should not return arrays
#pragma warning disable CA2000 // Don't actually need to dispose FakeEmbeddingGenerator
#pragma warning disable CS8605 // Unboxing a possibly null value.

public abstract class EmbeddingGenerationTests<TKey>(EmbeddingGenerationTests<TKey>.Fixture fixture)
    where TKey : notnull
{
    #region Search

    [ConditionalFact]
    public virtual async Task SearchAsync_with_property_generator()
    {
        // Property level: embedding generators are defined at all levels. The property generator should take precedence.
        var collection = this.GetCollection<Record>(storeGenerator: true, collectionGenerator: true, propertyGenerator: true);

        var result = await collection.SearchAsync("[1, 1, 0]", top: 1).SingleAsync();

        Assert.Equal("Property ([1, 1, 3])", result.Record.Text);
    }

    [ConditionalFact]
    public virtual async Task SearchAsync_with_property_generator_dynamic()
    {
        // Property level: embedding generators are defined at all levels. The property generator should take precedence.
        var collection = this.GetCollection<Dictionary<string, object?>>(storeGenerator: true, collectionGenerator: true, propertyGenerator: true);

        var result = await collection.SearchAsync("[1, 1, 0]", top: 1).SingleAsync();

        Assert.Equal("Property ([1, 1, 3])", result.Record[nameof(Record.Text)]);
    }

    [ConditionalFact]
    public virtual async Task SearchAsync_with_collection_generator()
    {
        // Collection level: embedding generators are defined at the collection and store level - the collection generator should take precedence.
        var collection = this.GetCollection<Record>(storeGenerator: true, collectionGenerator: true, propertyGenerator: false);

        var result = await collection.SearchAsync("[1, 1, 0]", top: 1).SingleAsync();

        Assert.Equal("Collection ([1, 1, 2])", result.Record.Text);
    }

    [ConditionalFact]
    public virtual async Task SearchAsync_with_store_generator()
    {
        // Store level: an embedding generator is defined at the store level only.
        var collection = this.GetCollection<Record>(storeGenerator: true, collectionGenerator: false, propertyGenerator: false);

        var result = await collection.SearchAsync("[1, 1, 0]", top: 1).SingleAsync();

        Assert.Equal("Store ([1, 1, 1])", result.Record.Text);
    }

    [ConditionalFact]
    public virtual async Task SearchAsync_with_store_dependency_injection()
    {
        foreach (var registrationDelegate in fixture.DependencyInjectionStoreRegistrationDelegates)
        {
            IServiceCollection serviceCollection = new ServiceCollection();

            serviceCollection.AddSingleton<IEmbeddingGenerator>(new FakeEmbeddingGenerator(replaceLast: 1));
            registrationDelegate(serviceCollection);

            await using var serviceProvider = serviceCollection.BuildServiceProvider();

            var vectorStore = serviceProvider.GetRequiredService<IVectorStore>();
            var collection = vectorStore.GetCollection<TKey, Record>(fixture.CollectionName, fixture.GetRecordDefinition());

            var result = await collection.SearchAsync("[1, 1, 0]", top: 1).SingleAsync();

            Assert.Equal("Store ([1, 1, 1])", result.Record.Text);
        }
    }

    [ConditionalFact]
    public virtual async Task SearchAsync_with_collection_dependency_injection()
    {
        foreach (var registrationDelegate in fixture.DependencyInjectionCollectionRegistrationDelegates)
        {
            IServiceCollection serviceCollection = new ServiceCollection();

            serviceCollection.AddSingleton<IEmbeddingGenerator>(new FakeEmbeddingGenerator(replaceLast: 1));
            registrationDelegate(serviceCollection);

            await using var serviceProvider = serviceCollection.BuildServiceProvider();

            var collection = serviceProvider.GetRequiredService<IVectorStoreRecordCollection<TKey, RecordWithAttributes>>();

            var result = await collection.SearchAsync("[1, 1, 0]", top: 1).SingleAsync();

            Assert.Equal("Store ([1, 1, 1])", result.Record.Text);
        }
    }

    [ConditionalFact]
    public virtual async Task SearchAsync_with_custom_input_type()
    {
        var recordDefinition = new VectorStoreRecordDefinition()
        {
            Properties = fixture.GetRecordDefinition().Properties
                .Select(p => p is VectorStoreRecordVectorProperty vectorProperty
                    ? new VectorStoreRecordVectorProperty<Customer>(nameof(Record.Embedding), dimensions: 3)
                    {
                        DistanceFunction = fixture.DefaultDistanceFunction,
                        IndexKind = fixture.DefaultIndexKind
                    }
                    : p)
                .ToList()
        };

        var collection = fixture.GetCollection<RecordWithCustomerVectorProperty>(
            fixture.CreateVectorStore(new FakeCustomerEmbeddingGenerator([1, 1, 1])),
            fixture.CollectionName,
            recordDefinition);

        var result = await collection.SearchAsync(new Customer(), top: 1).SingleAsync();

        Assert.Equal("Store ([1, 1, 1])", result.Record.Text);
    }

    [ConditionalFact]
    public virtual async Task SearchAsync_without_generator_throws()
    {
        // The database doesn't support embedding generation, and no client-side generator has been configured at any level,
        // so SearchAsync should throw.
        var collection = fixture.GetCollection<RawRecord>(fixture.TestStore.DefaultVectorStore, fixture.CollectionName + "WithoutGenerator");

        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() => collection.SearchAsync("foo", top: 1).ToListAsync().AsTask());

        Assert.Equal(VectorDataStrings.NoEmbeddingGeneratorWasConfiguredForSearch, exception.Message);
    }

    public class RawRecord
    {
        [VectorStoreRecordKey]
        public TKey Key { get; set; } = default!;
        [VectorStoreRecordVector(Dimensions: 3)]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }

    [ConditionalFact]
    public virtual async Task SearchAsync_with_embedding_argument_throws()
    {
        var collection = this.GetCollection<Record>(storeGenerator: true, collectionGenerator: true, propertyGenerator: true);

        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() => collection.SearchAsync(new ReadOnlyMemory<float>([1, 2, 3]), top: 1).ToListAsync().AsTask());

        Assert.Equal(VectorDataStrings.EmbeddingTypePassedToSearchAsync, exception.Message);
    }

    [ConditionalFact]
    public virtual async Task SearchAsync_with_incompatible_generator_throws()
    {
        var collection = this.GetCollection<Record>(storeGenerator: true, collectionGenerator: true, propertyGenerator: true);

        // We have a generator configured for string, not int.
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() => collection.SearchAsync(8, top: 1).ToListAsync().AsTask());

        Assert.Equal($"An input of type 'Int32' was provided, but an incompatible embedding generator of type '{nameof(FakeEmbeddingGenerator)}' was configured.", exception.Message);
    }

    #endregion Search

    #region Upsert

    [ConditionalFact]
    public virtual async Task UpsertAsync()
    {
        var counter = fixture.GenerateNextCounter();

        var record = new Record
        {
            Key = fixture.GenerateNextKey<TKey>(),
            Embedding = "[100, 1, 0]",
            Counter = counter,
            Text = nameof(UpsertAsync)
        };

        // Property level: embedding generators are defined at all levels. The property generator should take precedence.
        var collection = this.GetCollection<Record>(storeGenerator: true, collectionGenerator: true, propertyGenerator: true);

        await collection.UpsertAsync(record).ConfigureAwait(false);

        await fixture.TestStore.WaitForDataAsync(collection, 1, filter: r => r.Counter == counter);

        var result = await collection.SearchEmbeddingAsync(new ReadOnlyMemory<float>([100, 1, 3]), top: 1).SingleAsync();
        Assert.Equal(counter, result.Record.Counter);
    }

    [ConditionalFact]
    public virtual async Task UpsertAsync_dynamic()
    {
        var counter = fixture.GenerateNextCounter();

        var record = new Dictionary<string, object?>
        {
            [nameof(Record.Key)] = fixture.GenerateNextKey<TKey>(),
            [nameof(Record.Embedding)] = "[200, 1, 0]",
            [nameof(Record.Counter)] = counter,
            [nameof(Record.Text)] = nameof(UpsertAsync_dynamic)
        };

        // Property level: embedding generators are defined at all levels. The property generator should take precedence.
        var collection = this.GetCollection<Dictionary<string, object?>>(storeGenerator: true, collectionGenerator: true, propertyGenerator: true);

        await collection.UpsertAsync(record).ConfigureAwait(false);

        await fixture.TestStore.WaitForDataAsync(collection, 1, filter: r => (int)r[nameof(Record.Counter)] == counter);

        var result = await collection.SearchEmbeddingAsync(new ReadOnlyMemory<float>([200, 1, 3]), top: 1).SingleAsync();
        Assert.Equal(counter, result.Record[nameof(Record.Counter)]);
    }

    [ConditionalFact]
    public virtual async Task UpsertAsync_batch()
    {
        var (counter1, counter2) = (fixture.GenerateNextCounter(), fixture.GenerateNextCounter());

        Record[] records =
        [
            new()
            {
                Key = fixture.GenerateNextKey<TKey>(),
                Embedding = "[300, 1, 0]",
                Counter = counter1,
                Text = nameof(UpsertAsync_batch) + "1"
            },
            new()
            {
                Key = fixture.GenerateNextKey<TKey>(),
                Embedding = "[400, 1, 0]",
                Counter = counter2,
                Text = nameof(UpsertAsync_batch) + "2"
            }
        ];

        var collection = this.GetCollection<Record>(storeGenerator: true, collectionGenerator: true, propertyGenerator: true);

        await collection.UpsertAsync(records).ConfigureAwait(false);

        await fixture.TestStore.WaitForDataAsync(collection, 2, filter: r => (int)r.Counter == counter1 || (int)r.Counter == counter2);

        var result = await collection.SearchEmbeddingAsync(new ReadOnlyMemory<float>([300, 1, 3]), top: 1).SingleAsync();
        Assert.Equal(counter1, result.Record.Counter);

        result = await collection.SearchEmbeddingAsync(new ReadOnlyMemory<float>([400, 1, 3]), top: 1).SingleAsync();
        Assert.Equal(counter2, result.Record.Counter);
    }

    [ConditionalFact]
    public virtual async Task UpsertAsync_batch_dynamic()
    {
        var (counter1, counter2) = (fixture.GenerateNextCounter(), fixture.GenerateNextCounter());

        Dictionary<string, object?>[] records =
        [
            new()
            {
                [nameof(Record.Key)] = fixture.GenerateNextKey<TKey>(),
                [nameof(Record.Embedding)] = "[500, 1, 0]",
                [nameof(Record.Counter)] = counter1,
                [nameof(Record.Text)] = nameof(UpsertAsync_batch_dynamic) + "1"
            },
            new()
            {
                [nameof(Record.Key)] = fixture.GenerateNextKey<TKey>(),
                [nameof(Record.Embedding)] = "[600, 1, 0]",
                [nameof(Record.Counter)] = counter2,
                [nameof(Record.Text)] = nameof(UpsertAsync_batch_dynamic) + "2"
            }
        ];

        var collection = this.GetCollection<Dictionary<string, object?>>(storeGenerator: true, collectionGenerator: true, propertyGenerator: true);

        await collection.UpsertAsync(records).ConfigureAwait(false);

        await fixture.TestStore.WaitForDataAsync(collection, 2, filter: r => (int)r[nameof(Record.Counter)] == counter1 || (int)r[nameof(Record.Counter)] == counter2);

        var result = await collection.SearchEmbeddingAsync(new ReadOnlyMemory<float>([500, 1, 3]), top: 1).SingleAsync();
        Assert.Equal(counter1, result.Record[nameof(Record.Counter)]);

        result = await collection.SearchEmbeddingAsync(new ReadOnlyMemory<float>([600, 1, 3]), top: 1).SingleAsync();
        Assert.Equal(counter2, result.Record[nameof(Record.Counter)]);
    }

    #endregion Upsert

    #region IncludeVectors

    [ConditionalFact]
    public virtual async Task SearchAsync_with_IncludeVectors_throws()
    {
        var collection = this.GetCollection<Record>(storeGenerator: true, collectionGenerator: true, propertyGenerator: true);

        var exception = await Assert.ThrowsAsync<NotSupportedException>(() => collection.SearchAsync("[1, 0, 0]", top: 1, new() { IncludeVectors = true }).ToListAsync().AsTask());

        Assert.Equal("When an embedding generator is configured, `Include Vectors` cannot be enabled.", exception.Message);
    }

    [ConditionalFact]
    public virtual async Task GetAsync_with_IncludeVectors_throws()
    {
        var collection = this.GetCollection<Record>(storeGenerator: true, collectionGenerator: true, propertyGenerator: true);

        var exception = await Assert.ThrowsAsync<NotSupportedException>(() => collection.GetAsync(fixture.TestData[0].Key, new() { IncludeVectors = true }));

        Assert.Equal("When an embedding generator is configured, `Include Vectors` cannot be enabled.", exception.Message);
    }

    [ConditionalFact]
    public virtual async Task GetAsync_enumerable_with_IncludeVectors_throws()
    {
        var collection = this.GetCollection<Record>(storeGenerator: true, collectionGenerator: true, propertyGenerator: true);

        var exception = await Assert.ThrowsAsync<NotSupportedException>(() =>
            collection.GetAsync(
                [fixture.TestData[0].Key, fixture.TestData[1].Key],
                new() { IncludeVectors = true })
                .ToListAsync().AsTask());

        Assert.Equal("When an embedding generator is configured, `Include Vectors` cannot be enabled.", exception.Message);
    }

    #endregion IncludeVectors

    #region Support

    public class Record
    {
        public TKey Key { get; set; } = default!;
        public string? Embedding { get; set; }

        public int Counter { get; set; }
        public string? Text { get; set; }
    }

    public class RecordWithAttributes
    {
        [VectorStoreRecordKey]
        public TKey Key { get; set; } = default!;

        [VectorStoreRecordVector(Dimensions: 3)]
        public string? Embedding { get; set; }

        [VectorStoreRecordData(IsIndexed = true)]
        public int Counter { get; set; }

        [VectorStoreRecordData]
        public string? Text { get; set; }
    }

    public class RecordWithCustomerVectorProperty
    {
        public TKey Key { get; set; } = default!;
        public Customer? Embedding { get; set; }

        public int Counter { get; set; }
        public string? Text { get; set; }
    }

    public class Customer
    {
        public string? FirstName { get; set; }
        public string? LastName { get; set; }
    }

    private IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TRecord>(
        bool storeGenerator = false,
        bool collectionGenerator = false,
        bool propertyGenerator = false)
        where TRecord : notnull
    {
        var properties = fixture.GetRecordDefinition().Properties;

        properties = properties
            .Select(p => p is VectorStoreRecordVectorProperty vectorProperty && propertyGenerator
                ? new VectorStoreRecordVectorProperty(vectorProperty) { EmbeddingGenerator = new FakeEmbeddingGenerator(replaceLast: 3) }
                : p)
            .ToList();

        var recordDefinition = new VectorStoreRecordDefinition
        {
            EmbeddingGenerator = collectionGenerator ? new FakeEmbeddingGenerator(replaceLast: 2) : null,
            Properties = properties
        };

        return fixture.GetCollection<TRecord>(
            fixture.CreateVectorStore(storeGenerator ? new FakeEmbeddingGenerator(replaceLast: 1) : null),
            fixture.CollectionName,
            recordDefinition);
    }

    public abstract class Fixture : VectorStoreCollectionFixture<TKey, Record>
    {
        private int _counter;

        public override string CollectionName => "EmbeddingGenerationTests";

        public override VectorStoreRecordDefinition GetRecordDefinition()
            => new()
            {
                Properties =
                [
                    new VectorStoreRecordKeyProperty(nameof(Record.Key), typeof(TKey)),
                    new VectorStoreRecordVectorProperty(nameof(Record.Embedding), typeof(string), dimensions: 3)
                    {
                        DistanceFunction = this.DefaultDistanceFunction,
                        IndexKind = this.DefaultIndexKind
                    },

                    new VectorStoreRecordDataProperty(nameof(Record.Counter), typeof(int)) { IsIndexed = true },
                    new VectorStoreRecordDataProperty(nameof(Record.Text), typeof(string))
                ],
                EmbeddingGenerator = new FakeEmbeddingGenerator()
            };

        protected override List<Record> BuildTestData() =>
        [
            new()
            {
                Key = this.GenerateNextKey<TKey>(),
                Embedding = "[1, 1, 1]",
                Counter = this.GenerateNextCounter(),
                Text = "Store ([1, 1, 1])"
            },
            new()
            {
                Key = this.GenerateNextKey<TKey>(),
                Embedding = "[1, 1, 2]",
                Counter = this.GenerateNextCounter(),
                Text = "Collection ([1, 1, 2])"
            },
            new()
            {
                Key = this.GenerateNextKey<TKey>(),
                Embedding = "[1, 1, 3]",
                Counter = this.GenerateNextCounter(),
                Text = "Property ([1, 1, 3])"
            }
        ];

        public virtual IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TRecord>(
            IVectorStore vectorStore,
            string collectionName,
            VectorStoreRecordDefinition? recordDefinition = null)
            where TRecord : notnull
            => vectorStore.GetCollection<TKey, TRecord>(collectionName, recordDefinition);

        public abstract IVectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator = null);

        public abstract Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates { get; }
        public abstract Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates { get; }

        public virtual int GenerateNextCounter()
            => Interlocked.Increment(ref this._counter);
    }

    private sealed class FakeEmbeddingGenerator(int? replaceLast = null) : IEmbeddingGenerator<string, Embedding<float>>
    {
        public Task<GeneratedEmbeddings<Embedding<float>>> GenerateAsync(
            IEnumerable<string> values,
            EmbeddingGenerationOptions? options = null,
            CancellationToken cancellationToken = default)
        {
            var results = new GeneratedEmbeddings<Embedding<float>>();

            foreach (var value in values)
            {
                var vector = value.TrimStart('[').TrimEnd(']').Split(',').Select(s => float.Parse(s.Trim())).ToArray();

                if (replaceLast is not null)
                {
                    vector[vector.Length - 1] = replaceLast.Value;
                }

                results.Add(new Embedding<float>(vector));
            }

            return Task.FromResult(results);
        }

        public object? GetService(Type serviceType, object? serviceKey = null)
            => null;

        public void Dispose()
        {
        }
    }

    private sealed class FakeCustomerEmbeddingGenerator(float[] embedding) : IEmbeddingGenerator<Customer, Embedding<float>>
    {
        public Task<GeneratedEmbeddings<Embedding<float>>> GenerateAsync(IEnumerable<Customer> values, EmbeddingGenerationOptions? options = null, CancellationToken cancellationToken = default)
            => Task.FromResult(new GeneratedEmbeddings<Embedding<float>> { new(embedding) });

        public object? GetService(Type serviceType, object? serviceKey = null)
            => null;

        public void Dispose()
        {
        }
    }

    #endregion Support
}
