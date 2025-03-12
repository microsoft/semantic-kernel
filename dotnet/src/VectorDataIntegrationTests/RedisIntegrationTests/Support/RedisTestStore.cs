// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Redis;
using StackExchange.Redis;
using Testcontainers.Redis;
using VectorDataSpecificationTests.Support;

namespace RedisIntegrationTests.Support;

internal sealed class RedisTestStore : TestStore
{
    public static RedisTestStore Instance { get; } = new();

    private readonly RedisContainer _container = new RedisBuilder()
        .WithImage("redis/redis-stack")
        .Build();

    private IDatabase? _database;
    private RedisVectorStore? _defaultVectorStore;

    public IDatabase Database => this._database ?? throw new InvalidOperationException("Not initialized");

    public override IVectorStore DefaultVectorStore => this._defaultVectorStore ?? throw new InvalidOperationException("Not initialized");

    public RedisVectorStore GetVectorStore(RedisVectorStoreOptions options)
        => new(this.Database, options);

    private RedisTestStore()
    {
    }

    protected override async Task StartAsync()
    {
        await this._container.StartAsync();
        var redis = await ConnectionMultiplexer.ConnectAsync($"{this._container.Hostname}:{this._container.GetMappedPublicPort(6379)},connectTimeout=60000,connectRetry=5");
        this._database = redis.GetDatabase();
        this._defaultVectorStore = new(this._database);
    }

    protected override Task StopAsync()
        => this._container.StopAsync();
}
