// Copyright (c) Microsoft. All rights reserved.

// ==========================================================================================================
// The easier way to instantiate the Semantic Kernel is to use KernelBuilder.
// You can access the builder using Kernel.CreateBuilder().

using System.Diagnostics;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Core;

namespace DependencyInjection;

public class Kernel_Building(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public void BuildKernelUsingServiceCollection()
    {
        // For greater flexibility and to incorporate arbitrary services, KernelBuilder.Services
        // provides direct access to an underlying IServiceCollection.
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddLogging(c => c.AddConsole().SetMinimumLevel(LogLevel.Information))
            .AddHttpClient()
            .AddAzureOpenAIChatCompletion(
                deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                apiKey: TestConfiguration.AzureOpenAI.ApiKey,
                modelId: TestConfiguration.AzureOpenAI.ChatModelId);
        Kernel kernel2 = builder.Build();
    }

    [Fact]
    public void BuildKernelUsingServiceProvider()
    {
        // Every call to KernelBuilder.Build creates a new Kernel instance, with a new service provider
        // and a new plugin collection.
        var builder = Kernel.CreateBuilder();
        Debug.Assert(!ReferenceEquals(builder.Build(), builder.Build()));

        // KernelBuilder provides a convenient API for creating Kernel instances. However, it is just a
        // wrapper around a service collection, ultimately constructing a Kernel
        // using the public constructor that's available for anyone to use directly if desired.
        var services = new ServiceCollection();
        services.AddLogging(c => c.AddConsole().SetMinimumLevel(LogLevel.Information));
        services.AddHttpClient();
        services.AddAzureOpenAIChatCompletion(
            deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
            endpoint: TestConfiguration.AzureOpenAI.Endpoint,
            apiKey: TestConfiguration.AzureOpenAI.ApiKey,
            modelId: TestConfiguration.AzureOpenAI.ChatModelId);
        Kernel kernel4 = new(services.BuildServiceProvider());

        // Kernels can also be constructed and resolved via such a dependency injection container.
        services.AddTransient<Kernel>();
        Kernel kernel5 = services.BuildServiceProvider().GetRequiredService<Kernel>();
    }

    [Fact]
    public void BuildKernelUsingServiceCollectionExtension()
    {
        // In fact, the AddKernel method exists to simplify this, registering a singleton KernelPluginCollection
        // that can be populated automatically with all IKernelPlugins registered in the collection, and a
        // transient Kernel that can then automatically be constructed from the service provider and resulting
        // plugins collection.
        var services = new ServiceCollection();
        services.AddLogging(c => c.AddConsole().SetMinimumLevel(LogLevel.Information));
        services.AddHttpClient();
        services.AddKernel().AddAzureOpenAIChatCompletion(
            deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
            endpoint: TestConfiguration.AzureOpenAI.Endpoint,
            apiKey: TestConfiguration.AzureOpenAI.ApiKey,
            modelId: TestConfiguration.AzureOpenAI.ChatModelId);
        services.AddSingleton<KernelPlugin>(sp => KernelPluginFactory.CreateFromType<TimePlugin>(serviceProvider: sp));
        services.AddSingleton<KernelPlugin>(sp => KernelPluginFactory.CreateFromType<HttpPlugin>(serviceProvider: sp));
        Kernel kernel6 = services.BuildServiceProvider().GetRequiredService<Kernel>();
    }
}
