// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Qdrant.Client;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Models;
using Xunit;

namespace Qdrant.ConformanceTests;

public class QdrantDependencyInjectionTests
    : DependencyInjectionTests<QdrantVectorStore, QdrantCollection<ulong, SimpleRecord<ulong>>, ulong, SimpleRecord<ulong>>
{
    private const string Host = "localhost";
    private const int Port = 8080;
    private const string ApiKey = "fakeKey";

    protected override void PopulateConfiguration(ConfigurationManager configuration, object? serviceKey = null)
        => configuration.AddInMemoryCollection(
        [
            new(CreateConfigKey("Qdrant", serviceKey, "Host"), Host),
            new(CreateConfigKey("Qdrant", serviceKey, "Port"), Port.ToString()),
            new(CreateConfigKey("Qdrant", serviceKey, "ApiKey"), ApiKey),
        ]);

    private static string HostProvider(IServiceProvider sp, object? serviceKey = null)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection(CreateConfigKey("Qdrant", serviceKey, "Host")).Value!;

    private static int PortProvider(IServiceProvider sp, object? serviceKey = null)
        => int.Parse(sp.GetRequiredService<IConfiguration>().GetRequiredSection(CreateConfigKey("Qdrant", serviceKey, "Port")).Value!);

    private static string ApiKeyProvider(IServiceProvider sp, object? serviceKey = null)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection(CreateConfigKey("Qdrant", serviceKey, "ApiKey")).Value!;

    public override IEnumerable<Func<IServiceCollection, object?, string, ServiceLifetime, IServiceCollection>> CollectionDelegates
    {
        get
        {
            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services
                    .AddSingleton<QdrantClient>(sp => new QdrantClient(Host, Port, apiKey: ApiKey))
                    .AddQdrantCollection<ulong, SimpleRecord<ulong>>(name, lifetime: lifetime)
                : services
                    .AddSingleton<QdrantClient>(sp => new QdrantClient(Host, Port, apiKey: ApiKey))
                    .AddKeyedQdrantCollection<ulong, SimpleRecord<ulong>>(serviceKey, name, lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services.AddQdrantCollection<ulong, SimpleRecord<ulong>>(
                    name, Host, Port, apiKey: ApiKey, lifetime: lifetime)
                : services.AddKeyedQdrantCollection<ulong, SimpleRecord<ulong>>(
                    serviceKey, name, Host, Port, apiKey: ApiKey, lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services.AddQdrantCollection<ulong, SimpleRecord<ulong>>(
                    name, sp => new QdrantClient(HostProvider(sp), PortProvider(sp), apiKey: ApiKeyProvider(sp)), lifetime: lifetime)
                : services.AddKeyedQdrantCollection<ulong, SimpleRecord<ulong>>(
                    serviceKey, name, sp => new QdrantClient(HostProvider(sp, serviceKey), PortProvider(sp, serviceKey), apiKey: ApiKeyProvider(sp, serviceKey)), lifetime: lifetime);
        }
    }

    public override IEnumerable<Func<IServiceCollection, object?, ServiceLifetime, IServiceCollection>> StoreDelegates
    {
        get
        {
            yield return (services, serviceKey, lifetime) => serviceKey is null
                ? services.AddQdrantVectorStore(
                    Host, Port, apiKey: ApiKey, lifetime: lifetime)
                : services.AddKeyedQdrantVectorStore(
                    serviceKey, Host, Port, apiKey: ApiKey, lifetime: lifetime);

            yield return (services, serviceKey, lifetime) => serviceKey is null
                ? services
                    .AddSingleton<QdrantClient>(sp => new QdrantClient(Host, Port, apiKey: ApiKey))
                    .AddQdrantVectorStore(lifetime: lifetime)
                : services
                    .AddSingleton<QdrantClient>(sp => new QdrantClient(Host, Port, apiKey: ApiKey))
                    .AddKeyedQdrantVectorStore(serviceKey, lifetime: lifetime);
        }
    }

    [Fact]
    public void HostCantBeNullOrEmpty()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddQdrantVectorStore(host: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedQdrantVectorStore(serviceKey: "notNull", host: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddQdrantCollection<ulong, SimpleRecord<ulong>>(
            name: "notNull", host: null!));
        Assert.Throws<ArgumentException>(() => services.AddQdrantCollection<ulong, SimpleRecord<ulong>>(
            name: "notNull", host: ""));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedQdrantCollection<ulong, SimpleRecord<ulong>>(
            serviceKey: "notNull", name: "notNull", host: null!));
        Assert.Throws<ArgumentException>(() => services.AddKeyedQdrantCollection<ulong, SimpleRecord<ulong>>(
            serviceKey: "notNull", name: "notNull", host: ""));
    }
}
