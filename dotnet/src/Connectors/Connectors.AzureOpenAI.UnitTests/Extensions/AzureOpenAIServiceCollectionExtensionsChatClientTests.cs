// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.Extensions;

public class AzureOpenAIServiceCollectionExtensionsChatClientTests
{
    [Fact]
    public void AddAzureOpenAIChatClientNullArgsThrow()
    {
        // Arrange
        ServiceCollection services = null!;
        string deploymentName = "gpt-35-turbo";
        string endpoint = "https://test-endpoint.openai.azure.com/";
        string apiKey = "test_api_key";
        string serviceId = "test_service_id";
        string modelId = "gpt-35-turbo";

        // Act & Assert
        var exception = Assert.Throws<ArgumentNullException>(() => services.AddAzureOpenAIChatClient(deploymentName, endpoint, apiKey, serviceId, modelId));
        Assert.Equal("services", exception.ParamName);

        exception = Assert.Throws<ArgumentNullException>(() => services.AddAzureOpenAIChatClient(deploymentName, new AzureOpenAIClient(new Uri(endpoint), new ApiKeyCredential(apiKey)), serviceId, modelId));
        Assert.Equal("services", exception.ParamName);

        TokenCredential credential = DelegatedTokenCredential.Create((_, _) => new AccessToken(apiKey, DateTimeOffset.Now));
        exception = Assert.Throws<ArgumentNullException>(() => services.AddAzureOpenAIChatClient(deploymentName, endpoint, credential, serviceId, modelId));
        Assert.Equal("services", exception.ParamName);
    }

    [Fact]
    public void AddAzureOpenAIChatClientDefaultValidParametersRegistersService()
    {
        // Arrange
        var services = new ServiceCollection();
        string deploymentName = "gpt-35-turbo";
        string endpoint = "https://test-endpoint.openai.azure.com/";
        string apiKey = "test_api_key";
        string serviceId = "test_service_id";
        string modelId = "gpt-35-turbo";

        // Act
        services.AddAzureOpenAIChatClient(deploymentName, endpoint, apiKey, serviceId, modelId);

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var chatClient = serviceProvider.GetKeyedService<IChatClient>(serviceId);
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void AddAzureOpenAIChatClientWithCredentialValidParametersRegistersService()
    {
        // Arrange
        var services = new ServiceCollection();
        string deploymentName = "gpt-35-turbo";
        string endpoint = "https://test-endpoint.openai.azure.com/";
        TokenCredential credential = DelegatedTokenCredential.Create((_, _) => new AccessToken("test key", DateTimeOffset.Now));
        string serviceId = "test_service_id";
        string modelId = "gpt-35-turbo";

        // Act
        services.AddAzureOpenAIChatClient(deploymentName, endpoint, credential, serviceId, modelId);

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var chatClient = serviceProvider.GetKeyedService<IChatClient>(serviceId);
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void AddAzureOpenAIChatClientWithClientValidParametersRegistersService()
    {
        // Arrange
        var services = new ServiceCollection();
        string deploymentName = "gpt-35-turbo";
        string endpoint = "https://test-endpoint.openai.azure.com/";
        string apiKey = "test_api_key";
        var azureOpenAIClient = new AzureOpenAIClient(new Uri(endpoint), new ApiKeyCredential(apiKey));
        string serviceId = "test_service_id";
        string modelId = "gpt-35-turbo";

        // Act
        services.AddAzureOpenAIChatClient(deploymentName, azureOpenAIClient, serviceId, modelId);

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var chatClient = serviceProvider.GetKeyedService<IChatClient>(serviceId);
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void AddAzureOpenAIChatClientWorksWithKernel()
    {
        // Arrange
        var services = new ServiceCollection();
        string deploymentName = "gpt-35-turbo";
        string endpoint = "https://test-endpoint.openai.azure.com/";
        string apiKey = "test_api_key";
        string serviceId = "test_service_id";
        string modelId = "gpt-35-turbo";

        // Act
        services.AddAzureOpenAIChatClient(deploymentName, endpoint, apiKey, serviceId, modelId);
        services.AddKernel();

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var kernel = serviceProvider.GetRequiredService<Kernel>();

        var serviceFromCollection = serviceProvider.GetKeyedService<IChatClient>(serviceId);
        var serviceFromKernel = kernel.GetRequiredService<IChatClient>(serviceId);

        Assert.NotNull(serviceFromKernel);
        Assert.Same(serviceFromCollection, serviceFromKernel);
    }
}
