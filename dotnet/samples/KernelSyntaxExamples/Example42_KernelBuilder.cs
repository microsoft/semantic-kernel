// Copyright (c) Microsoft. All rights reserved.

// ==========================================================================================================
// The easier way to instantiate the Semantic Kernel is to use KernelBuilder.
// You can access the builder using new KernelBuilder().

#pragma warning disable CA1852

using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Core;

// ReSharper disable once InconsistentNaming
public static class Example42_KernelBuilder
{
    public static Task RunAsync()
    {
        string azureOpenAIKey = TestConfiguration.AzureOpenAI.ApiKey;
        string azureOpenAIEndpoint = TestConfiguration.AzureOpenAI.Endpoint;
        string azureOpenAIChatDeploymentName = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        string azureOpenAIChatModelId = TestConfiguration.AzureOpenAI.ChatModelId;
        string azureOpenAIEmbeddingDeployment = TestConfiguration.AzureOpenAIEmbeddings.DeploymentName;

        // KernelBuilder provides a simple way to configure a Kernel. This constructs a kernel
        // with logging and an Azure OpenAI chat completion service configured.
        Kernel kernel1 = new KernelBuilder()
            .AddAzureOpenAIChatCompletion(azureOpenAIChatDeploymentName, azureOpenAIChatModelId, azureOpenAIEndpoint, azureOpenAIKey)
            .Build();

        // For greater flexibility and to incorporate arbitrary services, KernelBuilder.Services
        // provides direct access to an underlying IServiceCollection.
        KernelBuilder builder = new();
        builder.Services.AddLogging(c => c.AddConsole().SetMinimumLevel(LogLevel.Information))
                        .AddHttpClient()
                        .AddAzureOpenAIChatCompletion(azureOpenAIChatDeploymentName, azureOpenAIChatModelId, azureOpenAIEndpoint, azureOpenAIKey);
        Kernel kernel2 = builder.Build();

        // Plugins may also be configured via the corresponding Plugins property.
        builder = new KernelBuilder();
        builder.Plugins.AddFromType<HttpPlugin>();
        Kernel kernel3 = builder.Build();

        // Every call to KernelBuilder.Build creates a new Kernel instance, with a new service provider
        // and a new plugin collection.
        builder = new KernelBuilder();
        Debug.Assert(!ReferenceEquals(builder.Build(), builder.Build()));

        // KernelBuilder provides a convenient API for creating Kernel instances. However, it is just a
        // wrapper around a service collection, ultimately constructing a Kernel
        // using the public constructor that's available for anyone to use directly if desired.
        var services = new ServiceCollection();
        services.AddLogging(c => c.AddConsole().SetMinimumLevel(LogLevel.Information));
        services.AddHttpClient();
        services.AddAzureOpenAIChatCompletion(azureOpenAIChatDeploymentName, azureOpenAIChatModelId, azureOpenAIEndpoint, azureOpenAIKey);
        Kernel kernel4 = new(services.BuildServiceProvider());

        // Kernels can also be constructed and resolved via such a dependency injection container.
        services.AddTransient<Kernel>();
        Kernel kernel5 = services.BuildServiceProvider().GetRequiredService<Kernel>();

        // In fact, the AddKernel method exists to simplify this, registering a singleton KernelPluginCollection
        // that can be populated automatically with all IKernelPlugins registered in the collection, and a
        // transient Kernel that can then automatically be constructed from the service provider and resulting
        // plugins collection.
        services = new ServiceCollection();
        services.AddLogging(c => c.AddConsole().SetMinimumLevel(LogLevel.Information));
        services.AddHttpClient();
        services.AddKernel().AddAzureOpenAIChatCompletion(azureOpenAIChatDeploymentName, azureOpenAIChatModelId, azureOpenAIEndpoint, azureOpenAIKey);
        services.AddSingleton<IKernelPlugin>(sp => KernelPluginFactory.CreateFromType<TimePlugin>(serviceProvider: sp));
        services.AddSingleton<IKernelPlugin>(sp => KernelPluginFactory.CreateFromType<HttpPlugin>(serviceProvider: sp));
        Kernel kernel6 = services.BuildServiceProvider().GetRequiredService<Kernel>();

        return Task.CompletedTask;
    }
}
