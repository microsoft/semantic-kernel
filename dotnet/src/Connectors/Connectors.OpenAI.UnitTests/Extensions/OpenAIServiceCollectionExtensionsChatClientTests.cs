// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Extensions;

public class OpenAIServiceCollectionExtensionsChatClientTests
{
    [Fact]
    public void AddOpenAIChatClientNullArgsThrow()
    {
        // Arrange
        ServiceCollection services = null!;
        string modelId = "gpt-3.5-turbo";
        string apiKey = "test_api_key";
        string orgId = "test_org_id";
        string serviceId = "test_service_id";

        // Act & Assert
        var exception = Assert.Throws<ArgumentNullException>(() => services.AddOpenAIChatClient(modelId, apiKey, orgId, serviceId));
        Assert.Equal("services", exception.ParamName);

        exception = Assert.Throws<ArgumentNullException>(() => services.AddOpenAIChatClient(modelId, new OpenAIClient(apiKey), serviceId));
        Assert.Equal("services", exception.ParamName);

        using var httpClient = new HttpClient();
        exception = Assert.Throws<ArgumentNullException>(() => services.AddOpenAIChatClient(modelId, new Uri("http://localhost"), apiKey, orgId, serviceId, httpClient));
        Assert.Equal("services", exception.ParamName);
    }

    [Fact]
    public void AddOpenAIChatClientDefaultValidParametersRegistersService()
    {
        // Arrange
        var services = new ServiceCollection();
        string modelId = "gpt-3.5-turbo";
        string apiKey = "test_api_key";
        string orgId = "test_org_id";
        string serviceId = "test_service_id";

        // Act
        services.AddOpenAIChatClient(modelId, apiKey, orgId, serviceId);

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var chatClient = serviceProvider.GetKeyedService<IChatClient>(serviceId);
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void AddOpenAIChatClientOpenAIClientValidParametersRegistersService()
    {
        // Arrange
        var services = new ServiceCollection();
        string modelId = "gpt-3.5-turbo";
        var openAIClient = new OpenAIClient("test_api_key");
        string serviceId = "test_service_id";

        // Act
        services.AddOpenAIChatClient(modelId, openAIClient, serviceId);

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var chatClient = serviceProvider.GetKeyedService<IChatClient>(serviceId);
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void AddOpenAIChatClientCustomEndpointValidParametersRegistersService()
    {
        // Arrange
        var services = new ServiceCollection();
        string modelId = "gpt-3.5-turbo";
        string apiKey = "test_api_key";
        string orgId = "test_org_id";
        string serviceId = "test_service_id";
        using var httpClient = new HttpClient();
        // Act
        services.AddOpenAIChatClient(modelId, new Uri("http://localhost"), apiKey, orgId, serviceId, httpClient);
        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var chatClient = serviceProvider.GetKeyedService<IChatClient>(serviceId);
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void AddOpenAIChatClientWorksWithKernel()
    {
        var services = new ServiceCollection();
        string modelId = "gpt-3.5-turbo";
        string apiKey = "test_api_key";
        string orgId = "test_org_id";
        string serviceId = "test_service_id";

        // Act
        services.AddOpenAIChatClient(modelId, apiKey, orgId, serviceId);
        services.AddKernel();

        var serviceProvider = services.BuildServiceProvider();
        var kernel = serviceProvider.GetRequiredService<Kernel>();

        var serviceFromCollection = serviceProvider.GetKeyedService<IChatClient>(serviceId);
        var serviceFromKernel = kernel.GetRequiredService<IChatClient>(serviceId);

        Assert.NotNull(serviceFromKernel);
        Assert.Same(serviceFromCollection, serviceFromKernel);
    }
}
