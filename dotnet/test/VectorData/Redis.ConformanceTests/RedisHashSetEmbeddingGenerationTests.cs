// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Redis;
using Redis.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Redis.ConformanceTests;

public class RedisHashSetEmbeddingGenerationTests(RedisHashSetEmbeddingGenerationTests.StringVectorFixture stringVectorFixture, RedisHashSetEmbeddingGenerationTests.RomOfFloatVectorFixture romOfFloatVectorFixture)
    : EmbeddingGenerationTests<string>(stringVectorFixture, romOfFloatVectorFixture), IClassFixture<RedisHashSetEmbeddingGenerationTests.StringVectorFixture>, IClassFixture<RedisHashSetEmbeddingGenerationTests.RomOfFloatVectorFixture>
{
    public new class StringVectorFixture : EmbeddingGenerationTests<string>.StringVectorFixture
    {
        public override TestStore TestStore => RedisTestStore.HashSetInstance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => RedisTestStore.HashSetInstance.GetVectorStore(new() { StorageType = RedisStorageType.HashSet, EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
             services => services
                 .AddSingleton(RedisTestStore.HashSetInstance.Database)
                 .AddRedisVectorStore(optionsProvider: _ => new RedisVectorStoreOptions() { StorageType = RedisStorageType.HashSet})
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(RedisTestStore.HashSetInstance.Database)
                .AddRedisHashSetCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }

    public new class RomOfFloatVectorFixture : EmbeddingGenerationTests<string>.RomOfFloatVectorFixture
    {
        public override TestStore TestStore => RedisTestStore.HashSetInstance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => RedisTestStore.HashSetInstance.GetVectorStore(new() { StorageType = RedisStorageType.HashSet, EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
             services => services
                 .AddSingleton(RedisTestStore.HashSetInstance.Database)
                 .AddRedisVectorStore(optionsProvider: _ => new RedisVectorStoreOptions() { StorageType = RedisStorageType.HashSet})
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(RedisTestStore.HashSetInstance.Database)
                .AddRedisHashSetCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }
}
