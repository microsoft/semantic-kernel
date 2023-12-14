// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi;

public class RestApiOperationTests
{
    [Fact]
    public void ItShouldUseHostUrlIfNoOverrideProvided()
    {
        // Arrange
        var sut = new RestApiOperation(
            "fake_id",
            new Uri("https://fake-random-test-host"),
            "/",
            HttpMethod.Get,
            "fake_description",
            new List<RestApiOperationParameter>()
        );

        var arguments = new Dictionary<string, object?>();

        // Act
        var url = sut.BuildOperationUrl(arguments);

        // Assert
        Assert.Equal("https://fake-random-test-host/", url.OriginalString);
    }

    [Fact]
    public void ItShouldUseHostUrlOverrideIfProvided()
    {
        // Arrange
        var sut = new RestApiOperation(
            "fake_id",
            new Uri("https://fake-random-test-host"),
            "/",
            HttpMethod.Get,
            "fake_description",
            new List<RestApiOperationParameter>()
        );

        var fakeHostUrlOverride = "https://fake-random-test-host-override";

        var arguments = new Dictionary<string, object?>();

        // Act
        var url = sut.BuildOperationUrl(arguments, serverUrlOverride: new Uri(fakeHostUrlOverride));

        // Assert
        Assert.Equal(fakeHostUrlOverride, url.OriginalString.TrimEnd('/'));
    }

    [Fact]
    public void ItShouldReplacePathParametersByValuesFromArguments()
    {
        // Arrange
        var parameters = new List<RestApiOperationParameter> {
            new(
                name: "p1",
                type: "string",
                isRequired: true,
                expand: false,
                location: RestApiOperationParameterLocation.Path,
                style: RestApiOperationParameterStyle.Simple),
            new(
                name: "p2",
                type: "number",
                isRequired: true,
                expand: false,
                location: RestApiOperationParameterLocation.Path,
                style: RestApiOperationParameterStyle.Simple)
        };

        var sut = new RestApiOperation(
            "fake_id",
            new Uri("https://fake-random-test-host"),
            "/{p1}/{p2}/other_fake_path_section",
            HttpMethod.Get,
            "fake_description",
            parameters
        );

        var arguments = new Dictionary<string, object?>
        {
            { "p1", "v1" },
            { "p2", 34 }
        };

        // Act
        var url = sut.BuildOperationUrl(arguments);

        // Assert
        Assert.Equal("https://fake-random-test-host/v1/34/other_fake_path_section", url.OriginalString);
    }

    [Fact]
    public void ShouldBuildResourceUrlWithoutQueryString()
    {
        // Arrange
        var parameters = new List<RestApiOperationParameter> {
            new(
                name: "p1",
                type: "string",
                isRequired: false,
                expand: false,
                location: RestApiOperationParameterLocation.Query,
                defaultValue: "dv1"),
            new(
                name: "fake-path",
                type: "string",
                isRequired: false,
                expand: false,
                location: RestApiOperationParameterLocation.Path)
        };

        var sut = new RestApiOperation(
            "fake_id",
            new Uri("https://fake-random-test-host"),
            "{fake-path}/",
            HttpMethod.Get,
            "fake_description",
            parameters);

        var fakeHostUrlOverride = "https://fake-random-test-host-override";

        var arguments = new Dictionary<string, object?>
        {
            { "fake-path", "fake-path-value" },
        };

        // Act
        var url = sut.BuildOperationUrl(arguments, serverUrlOverride: new Uri(fakeHostUrlOverride));

        // Assert
        Assert.Equal($"{fakeHostUrlOverride}/fake-path-value/", url.OriginalString);
    }

    [Fact]
    public void ItShouldRenderHeaderValuesFromArguments()
    {
        // Arrange
        var parameters = new List<RestApiOperationParameter>
        {
            new(
                name: "fake_header_one",
                type: "string",
                isRequired: true,
                expand: false,
                location: RestApiOperationParameterLocation.Header,
                style: RestApiOperationParameterStyle.Simple),

            new(
                name: "fake_header_two",
                type: "string",
                isRequired: true,
                expand: false,
                location: RestApiOperationParameterLocation.Header,
                style: RestApiOperationParameterStyle.Simple)
        };

        var arguments = new Dictionary<string, object?>
        {
            { "fake_header_one", "fake_header_one_value" },
            { "fake_header_two", "fake_header_two_value" }
        };

        var sut = new RestApiOperation("fake_id", new Uri("http://fake_url"), "fake_path", HttpMethod.Get, "fake_description", parameters);

        // Act
        var headers = sut.BuildHeaders(arguments);

        // Assert
        Assert.Equal(2, headers.Count);

        var headerOne = headers["fake_header_one"];
        Assert.Equal("fake_header_one_value", headerOne);

        var headerTwo = headers["fake_header_two"];
        Assert.Equal("fake_header_two_value", headerTwo);
    }

    [Fact]
    public void ShouldThrowExceptionIfNoValueProvidedForRequiredHeader()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new(name: "fake_header_one", type: "string", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new(name: "fake_header_two", type : "string", isRequired : false, expand : false, location : RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple)
        };

        var sut = new RestApiOperation("fake_id", new Uri("http://fake_url"), "fake_path", HttpMethod.Get, "fake_description", metadata);

        // Act
        void Act() => sut.BuildHeaders(new Dictionary<string, object?>());

        // Assert
        Assert.Throws<KernelException>(Act);
    }

    [Fact]
    public void ItShouldSkipOptionalHeaderHavingNoValue()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new(name: "fake_header_one", type : "string", isRequired : true, expand : false, location : RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new(name: "fake_header_two", type : "string", isRequired : false, expand : false, location : RestApiOperationParameterLocation.Header, style : RestApiOperationParameterStyle.Simple)
        };

        var arguments = new Dictionary<string, object?>
        {
            ["fake_header_one"] = "fake_header_one_value"
        };

        var sut = new RestApiOperation("fake_id", new Uri("http://fake_url"), "fake_path", HttpMethod.Get, "fake_description", metadata);

        // Act
        var headers = sut.BuildHeaders(arguments);

        // Assert
        Assert.Single(headers);

        var headerOne = headers["fake_header_one"];
        Assert.Equal("fake_header_one_value", headerOne);
    }

    [Fact]
    public void ItShouldCreateHeaderWithCommaSeparatedValues()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new( name: "h1", type: "array", isRequired: false, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple, arrayItemType: "string"),
            new( name: "h2", type: "array", isRequired: false, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple, arrayItemType: "integer")
        };

        var arguments = new Dictionary<string, object?>
        {
            ["h1"] = "[\"a\",\"b\",\"c\"]",
            ["h2"] = "[1,2,3]"
        };

        var sut = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata);

        // Act
        var headers = sut.BuildHeaders(arguments);

        // Assert
        Assert.NotNull(headers);
        Assert.Equal(2, headers.Count);

        Assert.Equal("a,b,c", headers["h1"]);
        Assert.Equal("1,2,3", headers["h2"]);
    }

    [Fact]
    public void ItShouldCreateHeaderWithPrimitiveValue()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new( name: "h1", type: "string", isRequired: false, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new( name: "h2", type: "boolean", isRequired: false, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple)
        };

        var arguments = new Dictionary<string, object?>
        {
            ["h1"] = "v1",
            ["h2"] = true
        };

        var sut = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata);

        // Act
        var headers = sut.BuildHeaders(arguments);

        // Assert
        Assert.NotNull(headers);
        Assert.Equal(2, headers.Count);

        Assert.Equal("v1", headers["h1"]);
        Assert.Equal("true", headers["h2"]);
    }

    [Fact]
    public void ItShouldMixAndMatchHeadersOfDifferentValueTypes()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new(name: "h1", type: "array", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new(name: "h2", type: "boolean", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
        };

        var arguments = new Dictionary<string, object?>
        {
            ["h1"] = new List<string> { "a", "b" },
            ["h2"] = "false"
        };

        var sut = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata);

        // Act
        var headers = sut.BuildHeaders(arguments);

        // Assert
        Assert.NotNull(headers);
        Assert.Equal(2, headers.Count);

        Assert.Equal("a,b", headers["h1"]);
        Assert.Equal("false", headers["h2"]);
    }

    [Fact]
    public void ItCreatesNewKernelsOnEachBuild()
    {
        IKernelBuilder builder = Kernel.CreateBuilder();
        Assert.NotSame(builder.Build(), builder.Build());
    }

    [Fact]
    public void ItHasIdempotentServicesAndPlugins()
    {
        IKernelBuilder builder = Kernel.CreateBuilder();

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
        Kernel kernel = Kernel.CreateBuilder().Build();
        Assert.Empty(kernel.Data);
    }

    [Fact]
    public void ItDefaultsServiceSelectorToSingleton()
    {
        Kernel kernel = Kernel.CreateBuilder().Build();
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

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<IAIServiceSelector>(selector);
        kernel = builder.Build();
        Assert.Same(selector, kernel.Services.GetService<IAIServiceSelector>());
        Assert.Same(selector, kernel.ServiceSelector);
        Assert.Same(selector, kernel.GetRequiredService<IAIServiceSelector>());
    }

    private sealed class NopServiceSelector : IAIServiceSelector
    {
#pragma warning disable CS8769 // Nullability of reference types in type of parameter doesn't match implemented member (possibly because of nullability attributes).
        bool IAIServiceSelector.TrySelectAIService<T>(
#pragma warning restore CS8769
            Kernel kernel, KernelFunction function, KernelArguments arguments, out T? service, out PromptExecutionSettings? serviceSettings) where T : class =>
            throw new NotImplementedException();
    }

    [Fact]
    public void ItPropagatesPluginsToBuiltKernel()
    {
        KernelPlugin plugin1 = KernelPluginFactory.CreateFromFunctions("plugin1");
        KernelPlugin plugin2 = KernelPluginFactory.CreateFromFunctions("plugin2");

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Plugins.Add(plugin1);
        builder.Plugins.Add(plugin2);
        Kernel kernel = builder.Build();

        Assert.Contains(plugin1, kernel.Plugins);
        Assert.Contains(plugin2, kernel.Plugins);
    }

    [Fact]
    public void ItSuppliesServicesCollectionToPluginsBuilder()
    {
        IKernelBuilder builder = Kernel.CreateBuilder();
        Assert.Same(builder.Services, builder.Plugins.Services);
    }

    [Fact]
    public void ItBuildsServicesIntoKernel()
    {
        var builder = Kernel.CreateBuilder()
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
        Kernel kernel = Kernel.CreateBuilder()
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
        KernelPluginCollection plugins = new() { KernelPluginFactory.CreateFromFunctions("plugin1") };

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
        KernelPlugin plugin1 = KernelPluginFactory.CreateFromFunctions("plugin1");
        KernelPlugin plugin2 = KernelPluginFactory.CreateFromFunctions("plugin2");
        KernelPlugin plugin3 = KernelPluginFactory.CreateFromFunctions("plugin3");

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(plugin1);
        builder.Services.AddSingleton(plugin2);
        builder.Services.AddSingleton(plugin3);
        Kernel kernel = builder.Build();

        Assert.Equal(3, kernel.Plugins.Count);
    }

    [Fact]
    public void ItFindsPluginCollectionToUse()
    {
        KernelPlugin plugin1 = KernelPluginFactory.CreateFromFunctions("plugin1");
        KernelPlugin plugin2 = KernelPluginFactory.CreateFromFunctions("plugin2");
        KernelPlugin plugin3 = KernelPluginFactory.CreateFromFunctions("plugin3");

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<KernelPluginCollection>(_ => new(new[] { plugin1, plugin2, plugin3 }));

        Kernel kernel1 = builder.Build();
        Assert.Equal(3, kernel1.Plugins.Count);

        Kernel kernel2 = builder.Build();
        Assert.Equal(3, kernel2.Plugins.Count);

        Assert.NotSame(kernel1.Plugins, kernel2.Plugins);
    }

    [Fact]
    public void ItAddsTheRightTypesInAddKernel()
    {
        IServiceCollection sc = new ServiceCollection();

        IKernelBuilder builder = sc.AddKernel();
        Assert.NotNull(builder);
        Assert.Throws<InvalidOperationException>(() => builder.Build());

        builder.Services.AddSingleton<Dictionary<string, string>>(new Dictionary<string, string>());

        IServiceProvider provider = sc.BuildServiceProvider();

        Assert.NotNull(provider.GetService<Dictionary<string, string>>());
        Assert.NotNull(provider.GetService<KernelPluginCollection>());
        Assert.NotNull(provider.GetService<Kernel>());
    }
}
