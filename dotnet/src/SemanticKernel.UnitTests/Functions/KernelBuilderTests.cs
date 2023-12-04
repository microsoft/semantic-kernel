// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextGeneration;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextGeneration;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelBuilderTests
{
    [Fact]
    public void ItCreatesNewKernelsOnEachBuild()
    {
        KernelBuilder builder = new();
        Assert.NotSame(builder.Build(), builder.Build());

        builder.WithCulture(CultureInfo.InvariantCulture);
        Assert.NotSame(builder.Build(), builder.Build());
    }

    [Fact]
    public void ItReturnsItselfFromWitherMethods()
    {
        KernelBuilder builder = new();
        Assert.Same(builder, builder.WithCulture(CultureInfo.InvariantCulture));
        Assert.Same(builder, builder.WithLoggerFactory(NullLoggerFactory.Instance));
        Assert.Same(builder, builder.WithAIServiceSelector(null));
        Assert.Same(builder, builder.WithPlugins(plugins => { }));
        Assert.Same(builder, builder.WithPlugins((plugins, serviceProvider) => { }));
        Assert.Same(builder, builder.WithServices(services => { }));
    }

    [Fact]
    public void ItDefaultsDataToAnEmptyDictionary()
    {
        Kernel kernel = new KernelBuilder().Build();
        Assert.Empty(kernel.Data);
    }

    [Fact]
    public void ItSupportsResettingCulture()
    {
        CultureInfo last = new("fr-FR");

        KernelBuilder builder = new KernelBuilder().WithCulture(CultureInfo.CurrentCulture);
        Assert.Same(CultureInfo.CurrentCulture, builder.Build().Culture);

        builder.WithCulture(null);
        Assert.Same(CultureInfo.InvariantCulture, builder.Build().Culture);

        builder.WithCulture(last);
        Assert.Same(last, builder.Build().Culture);
    }

    [Fact]
    public void ItSupportsOverwritingCulture()
    {
        CultureInfo last = new("fr-FR");

        Kernel kernel = new KernelBuilder()
            .WithCulture(CultureInfo.InvariantCulture)
            .WithCulture(null)
            .WithCulture(CultureInfo.CurrentCulture)
            .WithCulture(last)
            .Build();

        Assert.Same(last, kernel.Culture);
    }

    [Fact]
    public void ItDefaultsCultureToInvariantCulture()
    {
        Kernel kernel = new KernelBuilder().Build();
        Assert.Same(CultureInfo.InvariantCulture, kernel.Culture);
    }

    [Fact]
    public void ItSupportsOverwritingLoggerFactory()
    {
        using ILoggerFactory loggerFactory1 = new LoggerFactory();
        using ILoggerFactory loggerFactory2 = new LoggerFactory();

        Kernel kernel = new KernelBuilder()
            .WithLoggerFactory(NullLoggerFactory.Instance)
            .WithLoggerFactory(loggerFactory1)
            .WithLoggerFactory(loggerFactory2)
            .Build();

        Assert.Same(loggerFactory2, kernel.GetService<ILoggerFactory>());
        Assert.Same(loggerFactory2, kernel.LoggerFactory);
    }

    [Fact]
    public void ItDefaultsLoggerFactoryToNullLoggerFactory()
    {
        Kernel kernel = new KernelBuilder().Build();
        Assert.Same(NullLoggerFactory.Instance, kernel.GetService<ILoggerFactory>());
        Assert.Same(NullLoggerFactory.Instance, kernel.LoggerFactory);
    }

    [Fact]
    public void ItPropagatesPluginsToBuiltKernel()
    {
        IKernelPlugin plugin1 = new KernelPlugin("plugin1");
        IKernelPlugin plugin2 = new KernelPlugin("plugin2");

        Kernel kernel = new KernelBuilder()
            .WithPlugins(plugins =>
            {
                Assert.NotNull(plugins);
                Assert.Empty(plugins);
                plugins.Add(plugin1);
                plugins.Add(plugin2);
            })
            .Build();

        Assert.Contains(plugin1, kernel.Plugins);
        Assert.Contains(plugin2, kernel.Plugins);
    }

    [Fact]
    public void ItAugmentsPluginsWithMultipleCalls()
    {
        IKernelPlugin plugin1 = new KernelPlugin("plugin1");
        IKernelPlugin plugin2 = new KernelPlugin("plugin2");

        // Delegate taking just plugins
        Kernel kernel = new KernelBuilder()
            .WithPlugins(plugins =>
            {
                Assert.NotNull(plugins);
                Assert.Empty(plugins);
                plugins.Add(plugin1);
            })
            .WithPlugins(plugins =>
            {
                Assert.Single(plugins);
                plugins.Add(plugin2);
            })
            .Build();
        Assert.Contains(plugin1, kernel.Plugins);
        Assert.Contains(plugin2, kernel.Plugins);

        // Delegate taking just serviceProvider and plugins
        kernel = new KernelBuilder()
            .WithPlugins((plugins, _) =>
            {
                Assert.NotNull(plugins);
                Assert.Empty(plugins);
                plugins.Add(plugin1);
            })
            .WithPlugins((plugins, _) =>
            {
                Assert.Single(plugins);
                plugins.Add(plugin2);
            })
            .Build();
        Assert.Contains(plugin1, kernel.Plugins);
        Assert.Contains(plugin2, kernel.Plugins);

        // Both combined
        kernel = new KernelBuilder()
            .WithPlugins(plugins =>
            {
                Assert.NotNull(plugins);
                Assert.Empty(plugins);
                plugins.Add(plugin1);
            })
            .WithPlugins((plugins, _) =>
            {
                Assert.Single(plugins);
                plugins.Add(plugin2);
            })
            .Build();
        Assert.Contains(plugin1, kernel.Plugins);
        Assert.Contains(plugin2, kernel.Plugins);
    }

    [Fact]
    public void ItSuppliesBuiltServiceProviderToConfigurePlugins()
    {
        using ILoggerFactory loggerFactory = new LoggerFactory();

        Kernel kernel = new KernelBuilder()
            .WithLoggerFactory(loggerFactory)
            .WithPlugins((plugins, serviceProvider) =>
            {
                Assert.Same(loggerFactory, serviceProvider.GetService(typeof(ILoggerFactory)));
            })
            .Build();
    }

    [Fact]
    public void ItBuildsServicesIntoKernel()
    {
        Kernel kernel = new KernelBuilder()
            .WithOpenAIChatCompletion(modelId: "abcd", apiKey: "efg", serviceId: "openai")
            .WithAzureOpenAITextGeneration(deploymentName: "hijk", modelId: "qrs", endpoint: "https://lmnop", apiKey: "tuv", serviceId: "azureopenai")
            .WithServices(services =>
            {
                services.AddSingleton<IFormatProvider>(CultureInfo.InvariantCulture);
                services.AddSingleton<IFormatProvider>(CultureInfo.CurrentCulture);
                services.AddSingleton<IFormatProvider>(new CultureInfo("en-US"));
            })
            .Build();

        Assert.IsType<OpenAIChatCompletionService>(kernel.GetService<IChatCompletionService>("openai"));
        Assert.IsType<AzureOpenAITextGenerationService>(kernel.GetService<ITextGenerationService>("azureopenai"));

        Assert.Equal(2, kernel.GetAllServices<ITextGenerationService>().Count());
        Assert.Single(kernel.GetAllServices<IChatCompletionService>());

        Assert.Equal(3, kernel.GetAllServices<IFormatProvider>().Count());
    }

    [Fact]
    public void ItSupportsMultipleEqualNamedServices()
    {
        Kernel kernel = new KernelBuilder()
            .WithOpenAIChatCompletion(modelId: "abcd", apiKey: "efg", serviceId: "openai")
            .WithOpenAIChatCompletion(modelId: "abcd", apiKey: "efg", serviceId: "openai")
            .WithOpenAIChatCompletion(modelId: "abcd", apiKey: "efg", serviceId: "openai")
            .WithOpenAIChatCompletion(modelId: "abcd", apiKey: "efg", serviceId: "openai")
            .WithAzureOpenAIChatCompletion(deploymentName: "hijk", modelId: "lmnop", endpoint: "https://qrs", apiKey: "tuv", serviceId: "openai")
            .WithAzureOpenAIChatCompletion(deploymentName: "hijk", modelId: "lmnop", endpoint: "https://qrs", apiKey: "tuv", serviceId: "openai")
            .WithAzureOpenAIChatCompletion(deploymentName: "hijk", modelId: "lmnop", endpoint: "https://qrs", apiKey: "tuv", serviceId: "openai")
            .WithAzureOpenAIChatCompletion(deploymentName: "hijk", modelId: "lmnop", endpoint: "https://qrs", apiKey: "tuv", serviceId: "openai")
            .Build();

        Assert.Equal(8, kernel.GetAllServices<IChatCompletionService>().Count());
    }

    [Fact]
    public void ItThrowsExceptionsWhereExpected()
    {
        KernelBuilder builder = new();

        Assert.Throws<ArgumentNullException>(() => builder.WithPlugins((Action<KernelPluginCollection>)null!));
        Assert.Throws<ArgumentNullException>(() => builder.WithPlugins((Action<KernelPluginCollection, IServiceProvider>)null!));
        Assert.Throws<ArgumentNullException>(() => builder.WithServices(null!));

        builder.WithLoggerFactory(null);
        builder.WithCulture(null);
        builder.WithAIServiceSelector(null);

        builder.Build();
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
        Assert.IsAssignableFrom<IChatCompletionService>(k.GetService<IChatCompletionService>("azureopenai1"));
        Assert.IsAssignableFrom<IChatCompletionService>(k.GetService<IChatCompletionService>("azureopenai2"));

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
}
