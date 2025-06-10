// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Connectors.Redis;
using Redis.ConformanceTests.Support;
using StackExchange.Redis;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Models;
using Xunit;

namespace Redis.ConformanceTests;

public class RedisJsonDependencyInjectionTests
    : DependencyInjectionTests<RedisVectorStore, RedisJsonCollection<string, SimpleRecord<string>>, string, SimpleRecord<string>>
{
    private const string ConnectionConfiguration = "localhost:6379";

    protected override void PopulateConfiguration(ConfigurationManager configuration, object? serviceKey = null)
        => configuration.AddInMemoryCollection(
        [
            new(CreateConfigKey("RedisJson", serviceKey, "Configuration"), ConnectionConfiguration),
        ]);

    private static string Provider(IServiceProvider sp, object? serviceKey = null)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection(CreateConfigKey("RedisJson", serviceKey, "Configuration")).Value!;

    public override IEnumerable<Func<IServiceCollection, object?, string, ServiceLifetime, IServiceCollection>> CollectionDelegates
    {
        get
        {
            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services
                    .AddRedisJsonCollection<SimpleRecord<string>>(name,
                        sp => new FakeDatabase(Provider(sp)), lifetime: lifetime)
                : services
                    .AddKeyedRedisJsonCollection<SimpleRecord<string>>(serviceKey, name,
                        sp => new FakeDatabase(Provider(sp, serviceKey)), lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services
                    .AddSingleton<IDatabase>(new FakeDatabase(ConnectionConfiguration))
                    .AddRedisJsonCollection<SimpleRecord<string>>(name, lifetime: lifetime)
                : services
                    .AddSingleton<IDatabase>(new FakeDatabase(ConnectionConfiguration))
                    .AddKeyedRedisJsonCollection<SimpleRecord<string>>(serviceKey, name, lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) => services
                    .AddKeyedSingleton<IDatabase>(serviceKey, new FakeDatabase(ConnectionConfiguration))
                    .AddKeyedRedisJsonCollection<SimpleRecord<string>>(serviceKey, name,
                        sp => sp.GetRequiredKeyedService<IDatabase>(serviceKey), lifetime: lifetime);
        }
    }

    public override IEnumerable<Func<IServiceCollection, object?, ServiceLifetime, IServiceCollection>> StoreDelegates
    {
        get
        {
            yield return (services, serviceKey, lifetime) => serviceKey is null
                ? services
                    .AddSingleton<IDatabase>(new FakeDatabase(ConnectionConfiguration))
                    .AddRedisVectorStore(lifetime: lifetime)
                : services
                    .AddSingleton<IDatabase>(new FakeDatabase(ConnectionConfiguration))
                    .AddKeyedRedisVectorStore(serviceKey, lifetime: lifetime);
        }
    }

    [Fact]
    public void ConnectionConfigurationCantBeNullOrEmpty()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddRedisVectorStore(connectionConfiguration: null!));
        Assert.Throws<ArgumentException>(() => services.AddRedisVectorStore(connectionConfiguration: ""));

        Assert.Throws<ArgumentNullException>(() => services.AddKeyedRedisVectorStore("serviceKey", connectionConfiguration: null!));
        Assert.Throws<ArgumentException>(() => services.AddKeyedRedisVectorStore("serviceKey", connectionConfiguration: ""));

        Assert.Throws<ArgumentNullException>(() => services.AddRedisJsonCollection<SimpleRecord<string>>(
            name: "notNull", connectionConfiguration: null!));
        Assert.Throws<ArgumentException>(() => services.AddRedisJsonCollection<SimpleRecord<string>>(
            name: "notNull", connectionConfiguration: ""));
    }
}
