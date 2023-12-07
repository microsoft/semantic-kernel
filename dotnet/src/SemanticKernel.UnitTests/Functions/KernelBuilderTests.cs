// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelBuilderTests
{
    [Fact]
    public void ItCreatesNewKernelsOnEachBuild()
    {
        KernelBuilder builder = new();
        Assert.NotSame(builder.Build(), builder.Build());
    }

    [Fact]
    public void ItHasIdempotentServicesAndPlugins()
    {
        KernelBuilder builder = new();

        Assert.NotNull(builder.Services);
        Assert.NotNull(builder.Plugins);

        IServiceCollection services = builder.Services;
        IKernelBuilderPlugins plugins = builder.Plugins;

        for (int i = 0; i < 3; i++)
        {
            Assert.Same(services, builder.Services);
            Assert.Same(plugins, builder.Plugins);
            Assert.NotNull(builder.Build());
        }
    }

    [Fact]
    public void ItDefaultsDataToAnEmptyDictionary()
    {
        Kernel kernel = new KernelBuilder().Build();
        Assert.Empty(kernel.Data);
    }

    [Fact]
    public void ItDefaultsServiceSelectorToSingleton()
    {
        Kernel kernel = new KernelBuilder().Build();
        Assert.Null(kernel.Services.GetService<IAIServiceSelector>());
        Assert.NotNull(kernel.ServiceSelector);
        Assert.Same(kernel.ServiceSelector, kernel.ServiceSelector);
        Assert.Throws<KernelException>(() => kernel.GetRequiredService<IAIServiceSelector>());

        kernel = new Kernel();
        Assert.Null(kernel.Services.GetService<IAIServiceSelector>());
        Assert.NotNull(kernel.ServiceSelector);
        Assert.Same(kernel.ServiceSelector, kernel.ServiceSelector);
        Assert.Throws<KernelException>(() => kernel.GetRequiredService<IAIServiceSelector>());

        NopServiceSelector selector = new();

        KernelBuilder builder = new();
        builder.Services.AddSingleton<IAIServiceSelector>(selector);
        kernel = builder.Build();
        Assert.Same(selector, kernel.Services.GetService<IAIServiceSelector>());
        Assert.Same(selector, kernel.ServiceSelector);
        Assert.Same(selector, kernel.GetRequiredService<IAIServiceSelector>());
    }

    private sealed class NopServiceSelector : IAIServiceSelector
    {
        (T?, PromptExecutionSettings?) IAIServiceSelector.SelectAIService<T>(Kernel kernel, KernelFunction function, KernelArguments arguments) where T : class =>
            throw new NotImplementedException();
    }

    [Fact]
    public void ItPropagatesPluginsToBuiltKernel()
    {
        IKernelPlugin plugin1 = new KernelPlugin("plugin1");
        IKernelPlugin plugin2 = new KernelPlugin("plugin2");

        KernelBuilder builder = new();
        builder.Plugins.Add(plugin1);
        builder.Plugins.Add(plugin2);
        Kernel kernel = builder.Build();

        Assert.Contains(plugin1, kernel.Plugins);
        Assert.Contains(plugin2, kernel.Plugins);
    }

    [Fact]
    public void ItSuppliesServicesCollectionToPluginsBuilder()
    {
        KernelBuilder builder = new();
        Assert.Same(builder.Services, builder.Plugins.Services);
    }

    [Fact]
    public void ItBuildsServicesIntoKernel()
    {
        var builder = new KernelBuilder()
            .AddOpenAIChatCompletion(modelId: "abcd", apiKey: "efg", serviceId: "openai")
            .AddAzureOpenAITextGeneration(deploymentName: "hijk", modelId: "qrs", endpoint: "https://lmnop", apiKey: "tuv", serviceId: "azureopenai");

        builder.Services.AddSingleton<IFormatProvider>(CultureInfo.InvariantCulture);
        builder.Services.AddSingleton<IFormatProvider>(CultureInfo.CurrentCulture);
        builder.Services.AddSingleton<IFormatProvider>(new CultureInfo("en-US"));

        Kernel kernel = builder.Build();

        Assert.IsType<OpenAIChatCompletionService>(kernel.GetRequiredService<IChatCompletionService>("openai"));
        Assert.IsType<AzureOpenAITextGenerationService>(kernel.GetRequiredService<ITextGenerationService>("azureopenai"));

        Assert.Equal(2, kernel.GetAllServices<ITextGenerationService>().Count());
        Assert.Single(kernel.GetAllServices<IChatCompletionService>());

        Assert.Equal(3, kernel.GetAllServices<IFormatProvider>().Count());
    }

    [Fact]
    public void ItSupportsMultipleEqualNamedServices()
    {
        Kernel kernel = new KernelBuilder()
            .AddOpenAIChatCompletion(modelId: "abcd", apiKey: "efg", serviceId: "openai")
            .AddOpenAIChatCompletion(modelId: "abcd", apiKey: "efg", serviceId: "openai")
            .AddOpenAIChatCompletion(modelId: "abcd", apiKey: "efg", serviceId: "openai")
            .AddOpenAIChatCompletion(modelId: "abcd", apiKey: "efg", serviceId: "openai")
            .AddAzureOpenAIChatCompletion(deploymentName: "hijk", modelId: "lmnop", endpoint: "https://qrs", apiKey: "tuv", serviceId: "openai")
            .AddAzureOpenAIChatCompletion(deploymentName: "hijk", modelId: "lmnop", endpoint: "https://qrs", apiKey: "tuv", serviceId: "openai")
            .AddAzureOpenAIChatCompletion(deploymentName: "hijk", modelId: "lmnop", endpoint: "https://qrs", apiKey: "tuv", serviceId: "openai")
            .AddAzureOpenAIChatCompletion(deploymentName: "hijk", modelId: "lmnop", endpoint: "https://qrs", apiKey: "tuv", serviceId: "openai")
            .Build();

        Assert.Equal(8, kernel.GetAllServices<IChatCompletionService>().Count());
    }

    [Fact]
    public void ItIsntNeededInDIContexts()
    {
        KernelPluginCollection plugins = new() { new KernelPlugin("plugin1") };

        var serviceCollection = new ServiceCollection();
        serviceCollection.AddAzureOpenAIChatCompletion(deploymentName: "abcd", modelId: "efg", endpoint: "https://hijk", apiKey: "lmnop");
        serviceCollection.AddAzureOpenAIChatCompletion(deploymentName: "abcd", modelId: "efg", endpoint: "https://hijk", apiKey: "lmnop");
        serviceCollection.AddAzureOpenAIChatCompletion(deploymentName: "abcd", modelId: "efg", endpoint: "https://hijk", apiKey: "lmnop", serviceId: "azureopenai1");
        serviceCollection.AddAzureOpenAIChatCompletion(deploymentName: "abcd", modelId: "efg", endpoint: "https://hijk", apiKey: "lmnop", serviceId: "azureopenai2");
        serviceCollection.AddSingleton(plugins);
        serviceCollection.AddSingleton<Kernel>();

        Kernel k = serviceCollection.BuildServiceProvider().GetService<Kernel>()!;

        Assert.NotNull(k);
        Assert.Same(plugins, k.Plugins);
        Assert.IsAssignableFrom<IChatCompletionService>(k.GetRequiredService<IChatCompletionService>("azureopenai1"));
        Assert.IsAssignableFrom<IChatCompletionService>(k.GetRequiredService<IChatCompletionService>("azureopenai2"));

        // This should be 4, not 2. However, there is currently a limitation with Microsoft.Extensions.DependencyInjection
        // that prevents GetAllServices from enumerating named services. KernelBuilder works around this,
        // but when just using DI directly, it will only find unnamed services. Once that issue is fixed and SK
        // brings in the new version, it can update the GetAllServices implementation to remove the workaround,
        // and then this test should be updated accordingly.
        Assert.Equal(2, k.GetAllServices<IChatCompletionService>().Count());

        // It's possible to explicitly use the same workaround outside of KernelBuilder to get all services,
        // but it's not recommended.

        //** WORKAROUND
        Dictionary<Type, HashSet<object?>> mapping = new();
        foreach (var descriptor in serviceCollection)
        {
            if (!mapping.TryGetValue(descriptor.ServiceType, out HashSet<object?>? keys))
            {
                mapping[descriptor.ServiceType] = keys = new HashSet<object?>();
            }
            keys.Add(descriptor.ServiceKey);
        }
        serviceCollection.AddKeyedSingleton<Dictionary<Type, HashSet<object?>>>("KernelServiceTypeToKeyMappings", mapping);
        //**

        k = serviceCollection.BuildServiceProvider().GetService<Kernel>()!;
        Assert.Equal(4, k.GetAllServices<IChatCompletionService>().Count()); // now this is 4 as expected
    }

    [Fact]
    public void ItFindsAllPluginsToPopulatePluginsCollection()
    {
        KernelPlugin plugin1 = new("plugin1");
        KernelPlugin plugin2 = new("plugin2");
        KernelPlugin plugin3 = new("plugin3");

        KernelBuilder builder = new();
        builder.Services.AddSingleton<IKernelPlugin>(plugin1);
        builder.Services.AddSingleton<IKernelPlugin>(plugin2);
        builder.Services.AddSingleton<IKernelPlugin>(plugin3);
        Kernel kernel = builder.Build();

        Assert.Equal(3, kernel.Plugins.Count);
    }

    [Fact]
    public void ItFindsPluginCollectionToUse()
    {
        KernelPlugin plugin1 = new("plugin1");
        KernelPlugin plugin2 = new("plugin2");
        KernelPlugin plugin3 = new("plugin3");

        KernelBuilder builder = new();
        builder.Services.AddTransient<KernelPluginCollection>(_ => new(new[] { plugin1, plugin2, plugin3 }));

        Kernel kernel1 = builder.Build();
        Assert.Equal(3, kernel1.Plugins.Count);

        Kernel kernel2 = builder.Build();
        Assert.Equal(3, kernel2.Plugins.Count);

        Assert.NotSame(kernel1.Plugins, kernel2.Plugins);
    }
}
