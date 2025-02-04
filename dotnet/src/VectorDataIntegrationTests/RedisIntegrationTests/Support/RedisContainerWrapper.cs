// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.Redis;
using StackExchange.Redis;
using Testcontainers.Redis;

namespace RedisIntegrationTests.Support;

public class RedisContainerWrapper : IAsyncDisposable
{
    private static readonly RedisContainer s_container = new RedisBuilder()
        .WithImage("redis/redis-stack")
        .Build();
    private static IDatabase? s_database;
    private static RedisVectorStore? s_defaultVectorStore;

    private static readonly SemaphoreSlim s_lock = new(1, 1);
    private static int s_referenceCount;

    public IDatabase Database => s_database ?? throw new InvalidOperationException("Not initialized");
    public RedisVectorStore DefaultVectorStore => s_defaultVectorStore ?? throw new InvalidOperationException("Not initialized");

    private RedisContainerWrapper()
    {
    }

    public static async Task<RedisContainerWrapper> GetAsync()
    {
        await s_lock.WaitAsync();
        try
        {
            if (s_referenceCount++ == 0)
            {
                await s_container.StartAsync();
                var redis = await ConnectionMultiplexer.ConnectAsync($"{s_container.Hostname}:{s_container.GetMappedPublicPort(6379)},connectTimeout=60000,connectRetry=5");
                s_database = redis.GetDatabase();
                s_defaultVectorStore = new(s_database);
            }
        }
        finally
        {
            s_lock.Release();
        }

        return new();
    }

    public async ValueTask DisposeAsync()
    {
        await s_lock.WaitAsync();
        try
        {
            if (--s_referenceCount == 0)
            {
                await s_container.StopAsync();
            }
        }
        finally
        {
            s_lock.Release();
        }

        GC.SuppressFinalize(this);
    }
}
