// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.Redis;
using StackExchange.Redis;
using Testcontainers.Redis;
using VectorData.ConformanceTests.Support;

namespace Redis.ConformanceTests.Support;

#pragma warning restore CA2213 // Disposable fields should be disposed

internal sealed class RedisTestStore : TestStore
{
    public static RedisTestStore JsonInstance { get; } = new(RedisStorageType.Json);
    public static RedisTestStore HashSetInstance { get; } = new(RedisStorageType.HashSet);

    private readonly RedisContainer _container = new RedisBuilder()
        .WithImage("redis/redis-stack")
        .WithPortBinding(6379, assignRandomHostPort: true)
        .WithPortBinding(8001, assignRandomHostPort: true)
        .Build();

    private readonly RedisStorageType _storageType;
    private IDatabase? _database;

    private RedisTestStore(RedisStorageType storageType) => this._storageType = storageType;

    public IDatabase Database => this._database ?? throw new InvalidOperationException("Not initialized");

    public RedisVectorStore GetVectorStore(RedisVectorStoreOptions options)
        => new(this.Database, options);

    protected override async Task StartAsync()
    {
        await this._container.StartAsync();
        var redis = await ConnectionMultiplexer.ConnectAsync($"{this._container.Hostname}:{this._container.GetMappedPublicPort(6379)},connectTimeout=60000,connectRetry=5");
        this._database = redis.GetDatabase();
        this.DefaultVectorStore = new RedisVectorStore(this._database, new() { StorageType = this._storageType });
    }

    protected override Task StopAsync()
        => this._container.StopAsync();
}
