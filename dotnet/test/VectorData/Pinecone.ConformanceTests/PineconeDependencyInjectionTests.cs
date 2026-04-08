// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using VectorData.ConformanceTests;
using Xunit;

namespace Pinecone.ConformanceTests;

public class PineconeDependencyInjectionTests
    : DependencyInjectionTests<PineconeVectorStore, PineconeCollection<string, DependencyInjectionTests<string>.Record>, string, DependencyInjectionTests<string>.Record>
{
    private const string ApiKey = "Fake API Key";
    private static readonly ClientOptions s_clientOptions = new() { MaxRetries = 1 };

    protected override string CollectionName => "lowercase";

    protected override void PopulateConfiguration(ConfigurationManager configuration, object? serviceKey = null)
        => configuration.AddInMemoryCollection(
        [
            new(CreateConfigKey("Pinecone", serviceKey, "ApiKey"), ApiKey),
        ]);

    private static string ApiKeyProvider(IServiceProvider sp, object? serviceKey = null)
        => sp.GetRequiredService<IConfiguration>().GetRequiredSection(CreateConfigKey("Pinecone", serviceKey, "ApiKey")).Value!;

    private static ClientOptions ClientOptionsProvider(IServiceProvider sp, object? serviceKey = null) => s_clientOptions;

    public override IEnumerable<Func<IServiceCollection, object?, string, ServiceLifetime, IServiceCollection>> CollectionDelegates
    {
        get
        {
            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services
                    .AddSingleton<PineconeClient>(sp => new PineconeClient(ApiKey))
                    .AddPineconeCollection<Record>(name, lifetime: lifetime)
                : services
                    .AddSingleton<PineconeClient>(sp => new PineconeClient(ApiKey))
                    .AddKeyedPineconeCollection<Record>(serviceKey, name, lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services.AddPineconeCollection<Record>(
                    name, ApiKey, lifetime: lifetime)
                : services.AddKeyedPineconeCollection<Record>(
                    serviceKey, name, ApiKey, lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services.AddPineconeCollection<Record>(
                    name, sp => new PineconeClient(ApiKeyProvider(sp), ClientOptionsProvider(sp)), lifetime: lifetime)
                : services.AddKeyedPineconeCollection<Record>(
                    serviceKey, name, sp => new PineconeClient(ApiKeyProvider(sp, serviceKey), ClientOptionsProvider(sp, serviceKey)), lifetime: lifetime);
        }
    }

    public override IEnumerable<Func<IServiceCollection, object?, ServiceLifetime, IServiceCollection>> StoreDelegates
    {
        get
        {
            yield return (services, serviceKey, lifetime) => serviceKey is null
                ? services.AddPineconeVectorStore(
                    ApiKey, s_clientOptions, lifetime: lifetime)
                : services.AddKeyedPineconeVectorStore(
                    serviceKey, ApiKey, s_clientOptions, lifetime: lifetime);

            yield return (services, serviceKey, lifetime) => serviceKey is null
                ? services
                    .AddSingleton<PineconeClient>(sp => new PineconeClient(ApiKey))
                    .AddPineconeVectorStore(lifetime: lifetime)
                : services
                    .AddSingleton<PineconeClient>(sp => new PineconeClient(ApiKey))
                    .AddKeyedPineconeVectorStore(serviceKey, lifetime: lifetime);
        }
    }

    [Fact]
    public void ApiKeyCantBeNullOrEmpty()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddPineconeVectorStore(apiKey: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedPineconeVectorStore(serviceKey: "notNull", apiKey: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddPineconeCollection<Record>(
            name: "notNull", apiKey: null!));
        Assert.Throws<ArgumentException>(() => services.AddPineconeCollection<Record>(
            name: "notNull", apiKey: ""));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedPineconeCollection<Record>(
            serviceKey: "notNull", name: "notNull", apiKey: null!));
        Assert.Throws<ArgumentException>(() => services.AddKeyedPineconeCollection<Record>(
            serviceKey: "notNull", name: "notNull", apiKey: ""));
    }
}
