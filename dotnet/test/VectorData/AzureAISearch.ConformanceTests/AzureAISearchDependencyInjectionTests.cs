// Copyright (c) Microsoft. All rights reserved.

using Azure;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using VectorData.ConformanceTests;
using Xunit;

namespace AzureAISearch.ConformanceTests;

public class AzureAISearchDependencyInjectionTests
    : DependencyInjectionTests<AzureAISearchVectorStore, AzureAISearchCollection<string, DependencyInjectionTests<string>.Record>, string, DependencyInjectionTests<string>.Record>
{
    private static readonly Uri s_endpoint = new("https://localhost");
    private static readonly AzureKeyCredential s_keyCredential = new("fakeKey");

    protected override void PopulateConfiguration(ConfigurationManager configuration, object? serviceKey = null)
        => configuration.AddInMemoryCollection(
        [
            new(CreateConfigKey("AzureAI", serviceKey, "Endpoint"), "https://localhost"),
            new(CreateConfigKey("AzureAI", serviceKey, "Key"), "fakeKey"),
        ]);

    private static Uri EndpointProvider(IServiceProvider sp, object? serviceKey = null)
        => new(sp.GetRequiredService<IConfiguration>().GetRequiredSection(CreateConfigKey("AzureAI", serviceKey, "Endpoint")).Value!);

    private static AzureKeyCredential KeyProvider(IServiceProvider sp, object? serviceKey = null)
        => new(sp.GetRequiredService<IConfiguration>().GetRequiredSection(CreateConfigKey("AzureAI", serviceKey, "Key")).Value!);

    public override IEnumerable<Func<IServiceCollection, object?, string, ServiceLifetime, IServiceCollection>> CollectionDelegates
    {
        get
        {
            yield return (services, serviceKey, name, lifetime) => serviceKey is null
            ? services
                .AddAzureAISearchCollection<Record>(name,
                    sp => new SearchIndexClient(EndpointProvider(sp), KeyProvider(sp)), lifetime: lifetime)
            : services
                .AddKeyedAzureAISearchCollection<Record>(serviceKey, name,
                    sp => new SearchIndexClient(EndpointProvider(sp, serviceKey), KeyProvider(sp, serviceKey)), lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services
                    .AddSingleton<SearchIndexClient>(sp => new SearchIndexClient(s_endpoint, s_keyCredential))
                    .AddAzureAISearchCollection<Record>(name, lifetime: lifetime)
                : services
                    .AddSingleton<SearchIndexClient>(sp => new SearchIndexClient(s_endpoint, s_keyCredential))
                    .AddKeyedAzureAISearchCollection<Record>(serviceKey, name, lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services.AddAzureAISearchCollection<Record>(
                    name, s_endpoint, s_keyCredential, lifetime: lifetime)
                : services.AddKeyedAzureAISearchCollection<Record>(
                    serviceKey, name, s_endpoint, s_keyCredential, lifetime: lifetime);
        }
    }

    public override IEnumerable<Func<IServiceCollection, object?, ServiceLifetime, IServiceCollection>> StoreDelegates
    {
        get
        {
            yield return (services, serviceKey, lifetime) => serviceKey is null
                ? services
                    .AddAzureAISearchVectorStore(sp => new SearchIndexClient(EndpointProvider(sp), KeyProvider(sp)), lifetime: lifetime)
                : services
                    .AddKeyedAzureAISearchVectorStore(serviceKey, sp => new SearchIndexClient(EndpointProvider(sp, serviceKey), KeyProvider(sp, serviceKey)), lifetime: lifetime);

            yield return (services, serviceKey, lifetime) => serviceKey is null
                ? services.AddAzureAISearchVectorStore(
                    s_endpoint, s_keyCredential, lifetime: lifetime)
                : services.AddKeyedAzureAISearchVectorStore(
                    serviceKey, s_endpoint, s_keyCredential, lifetime: lifetime);

            yield return (services, serviceKey, lifetime) => serviceKey is null
                ? services
                    .AddSingleton<SearchIndexClient>(sp => new SearchIndexClient(s_endpoint, s_keyCredential))
                    .AddAzureAISearchVectorStore(lifetime: lifetime)
                : services
                    .AddSingleton<SearchIndexClient>(sp => new SearchIndexClient(s_endpoint, s_keyCredential))
                    .AddKeyedAzureAISearchVectorStore(serviceKey, lifetime: lifetime);
        }
    }

    [Fact]
    public void EndpointCantBeNull()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddAzureAISearchCollection<Record>(
            name: "notNull", endpoint: null!, s_keyCredential));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedAzureAISearchCollection<Record>(
            serviceKey: "notNull", name: "notNull", endpoint: null!, s_keyCredential));
    }

    [Fact]
    public void KeyCredentialCantBeNull()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddAzureAISearchCollection<Record>(
            name: "notNull", s_endpoint, keyCredential: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedAzureAISearchCollection<Record>(
            serviceKey: "notNull", name: "notNull", s_endpoint, keyCredential: null!));
    }

    [Fact]
    public void TokenCredentialCantBeNull()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddAzureAISearchCollection<Record>(
            name: "notNull", s_endpoint, tokenCredential: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedAzureAISearchCollection<Record>(
            serviceKey: "notNull", name: "notNull", s_endpoint, tokenCredential: null!));
    }
}
