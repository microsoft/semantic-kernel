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
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;
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
        Assert.Same(builder, builder.ConfigurePlugins(plugins => { }));
        Assert.Same(builder, builder.ConfigurePlugins((serviceProvider, plugins) => { }));
        Assert.Same(builder, builder.ConfigureServices(services => { }));
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
    }

    [Fact]
    public void ItPropagatesPluginsToBuiltKernel()
    {
        IKernelPlugin plugin1 = new KernelPlugin("plugin1");
        IKernelPlugin plugin2 = new KernelPlugin("plugin2");

        Kernel kernel = new KernelBuilder()
            .ConfigurePlugins(plugins =>
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
            .ConfigurePlugins(plugins =>
            {
                Assert.NotNull(plugins);
                Assert.Empty(plugins);
                plugins.Add(plugin1);
            })
            .ConfigurePlugins(plugins =>
            {
                Assert.Single(plugins);
                plugins.Add(plugin2);
            })
            .Build();
        Assert.Contains(plugin1, kernel.Plugins);
        Assert.Contains(plugin2, kernel.Plugins);

        // Delegate taking just serviceProvider and plugins
        kernel = new KernelBuilder()
            .ConfigurePlugins((_, plugins) =>
            {
                Assert.NotNull(plugins);
                Assert.Empty(plugins);
                plugins.Add(plugin1);
            })
            .ConfigurePlugins((_, plugins) =>
            {
                Assert.Single(plugins);
                plugins.Add(plugin2);
            })
            .Build();
        Assert.Contains(plugin1, kernel.Plugins);
        Assert.Contains(plugin2, kernel.Plugins);

        // Both combined
        kernel = new KernelBuilder()
            .ConfigurePlugins(plugins =>
            {
                Assert.NotNull(plugins);
                Assert.Empty(plugins);
                plugins.Add(plugin1);
            })
            .ConfigurePlugins((_, plugins) =>
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
            .ConfigurePlugins((serviceProvider, plugins) =>
            {
                Assert.Same(loggerFactory, serviceProvider.GetService(typeof(ILoggerFactory)));
            })
            .Build();
    }

    [Fact]
    public void ItBuildsServicesIntoKernel()
    {
        Kernel kernel = new KernelBuilder()
            .WithOpenAIChatCompletion("abcd", "efg", serviceId: "openai")
            .WithAzureOpenAITextCompletion("hijk", "https://lmnop", "qrs", serviceId: "azureopenai")
            .ConfigureServices(services =>
            {
                services.AddSingleton<IFormatProvider>(CultureInfo.InvariantCulture);
                services.AddSingleton<IFormatProvider>(CultureInfo.CurrentCulture);
                services.AddSingleton<IFormatProvider>(new CultureInfo("en-US"));
            })
            .Build();

        Assert.IsType<OpenAIChatCompletion>(kernel.GetService<IChatCompletion>("openai"));
        Assert.IsType<AzureOpenAITextCompletion>(kernel.GetService<ITextCompletion>("azureopenai"));

        Assert.Equal(2, kernel.GetAllServices<ITextCompletion>().Count());
        Assert.Single(kernel.GetAllServices<IChatCompletion>());

        Assert.Equal(3, kernel.GetAllServices<IFormatProvider>().Count());
    }

    [Fact]
    public void ItSupportsMultipleEqualNamedServices()
    {
        Kernel kernel = new KernelBuilder()
            .WithOpenAIChatCompletion("abcd", "efg", serviceId: "openai")
            .WithOpenAIChatCompletion("abcd", "efg", serviceId: "openai")
            .WithOpenAIChatCompletion("abcd", "efg", serviceId: "openai")
            .WithOpenAIChatCompletion("abcd", "efg", serviceId: "openai")
            .WithAzureOpenAIChatCompletion("hijk", "https://lmnop", "qrs", serviceId: "openai")
            .WithAzureOpenAIChatCompletion("hijk", "https://lmnop", "qrs", serviceId: "openai")
            .WithAzureOpenAIChatCompletion("hijk", "https://lmnop", "qrs", serviceId: "openai")
            .WithAzureOpenAIChatCompletion("hijk", "https://lmnop", "qrs", serviceId: "openai")
            .Build();

        Assert.Equal(8, kernel.GetAllServices<IChatCompletion>().Count());
    }

    [Fact]
    public void ItThrowsExceptionsWhereExpected()
    {
        KernelBuilder builder = new();

        Assert.Throws<ArgumentNullException>(() => builder.ConfigurePlugins((Action<ICollection<IKernelPlugin>>)null!));
        Assert.Throws<ArgumentNullException>(() => builder.ConfigurePlugins((Action<IServiceProvider, ICollection<IKernelPlugin>>)null!));
        Assert.Throws<ArgumentNullException>(() => builder.ConfigureServices(null!));

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
        serviceCollection.AddAzureOpenAIChatCompletion("abcd", "https://efg", "hijklmnop");
        serviceCollection.AddAzureOpenAIChatCompletion("abcd", "https://efg", "hijklmnop");
        serviceCollection.AddAzureOpenAIChatCompletion("abcd", "https://efg", "hijklmnop", serviceId: "azureopenai1");
        serviceCollection.AddAzureOpenAIChatCompletion("abcd", "https://efg", "hijklmnop", serviceId: "azureopenai2");
        serviceCollection.AddSingleton(plugins);
        serviceCollection.AddSingleton<Kernel>();

        Kernel k = serviceCollection.BuildServiceProvider().GetService<Kernel>()!;

        Assert.NotNull(k);
        Assert.Same(plugins, k.Plugins);
        Assert.IsAssignableFrom<IChatCompletion>(k.GetService<IChatCompletion>("azureopenai1"));
        Assert.IsAssignableFrom<IChatCompletion>(k.GetService<IChatCompletion>("azureopenai2"));

        // This should be 4, not 2. However, there is currently a limitation with Microsoft.Extensions.DependencyInjection
        // that prevents GetAllServices from enumerating named services. KernelBuilder works around this,
        // but when just using DI directly, it will only find unnamed services. Once that issue is fixed and SK
        // brings in the new version, it can update the GetAllServices implementation to remove the workaround,
        // and then this test should be updated accordingly.
        Assert.Equal(2, k.GetAllServices<IChatCompletion>().Count());
    }
}
