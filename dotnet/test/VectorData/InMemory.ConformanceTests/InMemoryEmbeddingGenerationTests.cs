// Copyright (c) Microsoft. All rights reserved.

using InMemory.ConformanceTests.Support;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace InMemory.ConformanceTests;

public class InMemoryEmbeddingGenerationTests(InMemoryEmbeddingGenerationTests.StringVectorFixture stringVectorFixture, InMemoryEmbeddingGenerationTests.RomOfFloatVectorFixture romOfFloatVectorFixture)
    : EmbeddingGenerationTests<int>(stringVectorFixture, romOfFloatVectorFixture), IClassFixture<InMemoryEmbeddingGenerationTests.StringVectorFixture>, IClassFixture<InMemoryEmbeddingGenerationTests.RomOfFloatVectorFixture>
{
    // InMemory doesn't allowing accessing the same collection via different .NET types (it's unique in this).
    // The following dynamic tests attempt to access the fixture collection - which is created with Record - via
    // Dictionary<string, object?>.
    public override Task SearchAsync_with_property_generator_dynamic() => Task.CompletedTask;
    public override Task UpsertAsync_dynamic() => Task.CompletedTask;
    public override Task UpsertAsync_batch_dynamic() => Task.CompletedTask;

    // The same applies to the custom type test:
    public override Task SearchAsync_with_custom_input_type() => Task.CompletedTask;

    // The test relies on creating a new InMemoryVectorStore configured with a store-default generator, but with InMemory that store
    // doesn't share the seeded data with the fixture store (since each InMemoryVectorStore has its own private data).
    // Test coverage is already largely sufficient via the property and collection tests.
    public override Task SearchAsync_with_store_generator() => Task.CompletedTask;

    public new class StringVectorFixture : EmbeddingGenerationTests<int>.StringVectorFixture
    {
        public override TestStore TestStore => InMemoryTestStore.Instance;

        // Note that with InMemory specifically, we can't create a vector store with an embedding generator, since it wouldn't share the seeded data with the fixture store.
        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => InMemoryTestStore.Instance.DefaultVectorStore;

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            // The InMemory DI methods register a new vector store instance, which doesn't share the collection seeded by the
            // fixture and the test fails.
            // services => services.AddInMemoryVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            // The InMemory DI methods register a new vector store instance, which doesn't share the collection seeded by the
            // fixture and the test fails.
            // services => services.AddInMemoryVectorStoreRecordCollection<int, RecordWithAttributes>(this.CollectionName)
        ];
    }

    public new class RomOfFloatVectorFixture : EmbeddingGenerationTests<int>.RomOfFloatVectorFixture
    {
        public override TestStore TestStore => InMemoryTestStore.Instance;

        // Note that with InMemory specifically, we can't create a vector store with an embedding generator, since it wouldn't share the seeded data with the fixture store.
        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => InMemoryTestStore.Instance.DefaultVectorStore;

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            // The InMemory DI methods register a new vector store instance, which doesn't share the collection seeded by the
            // fixture and the test fails.
            // services => services.AddInMemoryVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            // The InMemory DI methods register a new vector store instance, which doesn't share the collection seeded by the
            // fixture and the test fails.
            // services => services.AddInMemoryVectorStoreRecordCollection<int, RecordWithAttributes>(this.CollectionName)
        ];
    }
}
