// Copyright (c) Microsoft. All rights reserved.

using Azure;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Models;
using Xunit;

namespace AzureAISearch.ConformanceTests;

public class AzureAISearchDependencyInjectionTests
    : DependencyInjectionTests<AzureAISearchVectorStore, AzureAISearchCollection<string, SimpleRecord<string>>, string, SimpleRecord<string>>
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
                .AddAzureAISearchCollection<SimpleRecord<string>>(name,
                    sp => new SearchIndexClient(EndpointProvider(sp), KeyProvider(sp)), lifetime: lifetime)
            : services
                .AddKeyedAzureAISearchCollection<SimpleRecord<string>>(serviceKey, name,
                    sp => new SearchIndexClient(EndpointProvider(sp, serviceKey), KeyProvider(sp, serviceKey)), lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services
                    .AddSingleton<SearchIndexClient>(sp => new SearchIndexClient(s_endpoint, s_keyCredential))
                    .AddAzureAISearchCollection<SimpleRecord<string>>(name, lifetime: lifetime)
                : services
                    .AddSingleton<SearchIndexClient>(sp => new SearchIndexClient(s_endpoint, s_keyCredential))
                    .AddKeyedAzureAISearchCollection<SimpleRecord<string>>(serviceKey, name, lifetime: lifetime);

            yield return (services, serviceKey, name, lifetime) => serviceKey is null
                ? services.AddAzureAISearchCollection<SimpleRecord<string>>(
                    name, s_endpoint, s_keyCredential, lifetime: lifetime)
                : services.AddKeyedAzureAISearchCollection<SimpleRecord<string>>(
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

        Assert.Throws<ArgumentNullException>(() => services.AddAzureAISearchCollection<SimpleRecord<string>>(
            name: "notNull", endpoint: null!, s_keyCredential));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedAzureAISearchCollection<SimpleRecord<string>>(
            serviceKey: "notNull", name: "notNull", endpoint: null!, s_keyCredential));
    }

    [Fact]
    public void KeyCredentialCantBeNull()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddAzureAISearchCollection<SimpleRecord<string>>(
            name: "notNull", s_endpoint, keyCredential: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedAzureAISearchCollection<SimpleRecord<string>>(
            serviceKey: "notNull", name: "notNull", s_endpoint, keyCredential: null!));
    }

    [Fact]
    public void TokenCredentialCantBeNull()
    {
        IServiceCollection services = new ServiceCollection();

        Assert.Throws<ArgumentNullException>(() => services.AddAzureAISearchCollection<SimpleRecord<string>>(
            name: "notNull", s_endpoint, tokenCredential: null!));
        Assert.Throws<ArgumentNullException>(() => services.AddKeyedAzureAISearchCollection<SimpleRecord<string>>(
            serviceKey: "notNull", name: "notNull", s_endpoint, tokenCredential: null!));
    }
}
