// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using MongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace MongoDB.ConformanceTests;

public class MongoEmbeddingGenerationTests(MongoEmbeddingGenerationTests.StringVectorFixture stringVectorFixture, MongoEmbeddingGenerationTests.RomOfFloatVectorFixture romOfFloatVectorFixture)
    : EmbeddingGenerationTests<string>(stringVectorFixture, romOfFloatVectorFixture), IClassFixture<MongoEmbeddingGenerationTests.StringVectorFixture>, IClassFixture<MongoEmbeddingGenerationTests.RomOfFloatVectorFixture>
{
    public new class StringVectorFixture : EmbeddingGenerationTests<string>.StringVectorFixture
    {
        public override TestStore TestStore => MongoTestStore.Instance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => MongoTestStore.Instance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(MongoTestStore.Instance.Database)
                .AddMongoVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(MongoTestStore.Instance.Database)
                .AddMongoCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }

    public new class RomOfFloatVectorFixture : EmbeddingGenerationTests<string>.RomOfFloatVectorFixture
    {
        public override TestStore TestStore => MongoTestStore.Instance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => MongoTestStore.Instance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(MongoTestStore.Instance.Database)
                .AddMongoVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(MongoTestStore.Instance.Database)
                .AddMongoCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }
}
