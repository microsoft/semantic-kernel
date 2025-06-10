// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Models;
using Xunit;

namespace Weaviate.ConformanceTests;

public class WeaviateDependencyInjectionTests
    : DependencyInjectionTests<WeaviateVectorStore, WeaviateCollection<Guid, SimpleRecord<Guid>>, Guid, SimpleRecord<Guid>>
{
    private static readonly Uri s_endpoint = new("http://localhost");
    private const string ApiKey = "Fake API Key";

    protected override string CollectionName => "Uppercase";

    protected override void PopulateConfiguration(ConfigurationManager configuration, object? serviceKey = null)
        => configuration.AddInMemoryCollection(
        [
            new(CreateConfigKey("Weaviate", serviceKey, "Endpoint"), "http://localhost"),
            new(CreateConfigKey("Weaviate", serviceKey, "ApiKey"), ApiKey),
        ]);

    private static Uri EndpointProvider(IServiceProvider sp, object? serviceKey = null)
        => new(sp.GetRequiredService<IConfiguration>().GetRequiredSection(CreateConfigKey("Weaviate", serviceKey, "Endpoint")).Value!);

    private static string ApiKeyProvider(IServiceProvider sp, object? serviceKey = null)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection(CreateConfigKey("Weaviate", serviceKey, "ApiKey")).Value!;

    public override IEnumerable<Func<IServiceCollection, object?, string, ServiceLifetime, IServiceCollection>> CollectionDelegates
    {
        get
        {
            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services
                    .AddSingleton<WeaviateCollectionOptions>(sp => new WeaviateCollectionOptions() { Endpoint = EndpointProvider(sp), ApiKey = ApiKeyProvider(sp) })
                    .AddWeaviateCollection<SimpleRecord<Guid>>(name, lifetime: lifetime)
                : services
                    .AddSingleton<WeaviateCollectionOptions>(sp => new WeaviateCollectionOptions() { Endpoint = EndpointProvider(sp, serviceKey), ApiKey = ApiKeyProvider(sp, serviceKey) })
                    .AddKeyedWeaviateCollection<SimpleRecord<Guid>>(serviceKey, name, lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services.AddWeaviateCollection<SimpleRecord<Guid>>(name, s_endpoint, ApiKey, lifetime: lifetime)
                : services.AddKeyedWeaviateCollection<SimpleRecord<Guid>>(serviceKey, name, s_endpoint, ApiKey, lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) =>
                services.AddKeyedWeaviateCollection<SimpleRecord<Guid>>(serviceKey, name, s_endpoint, ApiKey, lifetime: lifetime);
        }
    }

    public override IEnumerable<Func<IServiceCollection, object?, ServiceLifetime, IServiceCollection>> StoreDelegates
    {
        get
        {
            yield return (services, serviceKey, lifetime) => serviceKey is null
                ? services.AddWeaviateVectorStore(s_endpoint, ApiKey, lifetime: lifetime)
                : services.AddKeyedWeaviateVectorStore(serviceKey, s_endpoint, ApiKey, lifetime: lifetime);

            yield return (services, serviceKey, lifetime) => serviceKey is null
                ? services
                    .AddSingleton<WeaviateVectorStoreOptions>(sp => new WeaviateVectorStoreOptions() { Endpoint = EndpointProvider(sp), ApiKey = ApiKeyProvider(sp) })
                    .AddWeaviateVectorStore(lifetime: lifetime)
                : services
                    .AddSingleton<WeaviateVectorStoreOptions>(sp => new WeaviateVectorStoreOptions() { Endpoint = EndpointProvider(sp, serviceKey), ApiKey = ApiKeyProvider(sp, serviceKey) })
                    .AddKeyedWeaviateVectorStore(serviceKey, lifetime: lifetime);
        }
    }

    [Fact]
    public void EndpointCantBeNull()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddWeaviateVectorStore(endpoint: null!, apiKey: ApiKey));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedWeaviateVectorStore(serviceKey: "notNull", endpoint: null!, apiKey: ApiKey));
        Assert.Throws<ArgumentNullException>(() => services.AddWeaviateCollection<SimpleRecord<Guid>>(
            name: "notNull", endpoint: null!, apiKey: ApiKey));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedWeaviateCollection<SimpleRecord<Guid>>(
            serviceKey: "notNull", name: "notNull", endpoint: null!, apiKey: ApiKey));
    }
}
