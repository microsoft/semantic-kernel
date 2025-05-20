// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.Extensions;

public class AzureOpenAIKernelBuilderExtensionsChatClientTests
{
    [Fact]
    public void AddAzureOpenAIChatClientNullArgsThrow()
    {
        // Arrange
        IKernelBuilder builder = null!;
        string deploymentName = "gpt-35-turbo";
        string endpoint = "https://test-endpoint.openai.azure.com/";
        string apiKey = "test_api_key";
        string serviceId = "test_service_id";
        string modelId = "gpt-35-turbo";

        // Act & Assert
        var exception = Assert.Throws<ArgumentNullException>(() => builder.AddAzureOpenAIChatClient(deploymentName, endpoint, apiKey, serviceId, modelId));
        Assert.Equal("builder", exception.ParamName);

        exception = Assert.Throws<ArgumentNullException>(() => builder.AddAzureOpenAIChatClient(deploymentName, new AzureOpenAIClient(new Uri(endpoint), new ApiKeyCredential(apiKey)), serviceId, modelId));
        Assert.Equal("builder", exception.ParamName);

        TokenCredential credential = DelegatedTokenCredential.Create((_, _) => new AccessToken(apiKey, DateTimeOffset.Now));
        exception = Assert.Throws<ArgumentNullException>(() => builder.AddAzureOpenAIChatClient(deploymentName, endpoint, credential, serviceId, modelId));
        Assert.Equal("builder", exception.ParamName);
    }

    [Fact]
    public void AddAzureOpenAIChatClientDefaultValidParametersRegistersService()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();
        string deploymentName = "gpt-35-turbo";
        string endpoint = "https://test-endpoint.openai.azure.com/";
        string apiKey = "test_api_key";
        string serviceId = "test_service_id";
        string modelId = "gpt-35-turbo";

        // Act
        builder.AddAzureOpenAIChatClient(deploymentName, endpoint, apiKey, serviceId, modelId);

        // Assert
        var kernel = builder.Build();
        Assert.NotNull(kernel.GetRequiredService<IChatClient>());
        Assert.NotNull(kernel.GetRequiredService<IChatClient>(serviceId));
    }

    [Fact]
    public void AddAzureOpenAIChatClientWithCredentialValidParametersRegistersService()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();
        string deploymentName = "gpt-35-turbo";
        string endpoint = "https://test-endpoint.openai.azure.com/";
        TokenCredential credential = DelegatedTokenCredential.Create((_, _) => new AccessToken("apiKey", DateTimeOffset.Now));
        string serviceId = "test_service_id";
        string modelId = "gpt-35-turbo";

        // Act
        builder.AddAzureOpenAIChatClient(deploymentName, endpoint, credential, serviceId, modelId);

        // Assert
        var kernel = builder.Build();
        Assert.NotNull(kernel.GetRequiredService<IChatClient>());
        Assert.NotNull(kernel.GetRequiredService<IChatClient>(serviceId));
    }

    [Fact]
    public void AddAzureOpenAIChatClientWithClientValidParametersRegistersService()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();
        string deploymentName = "gpt-35-turbo";
        string endpoint = "https://test-endpoint.openai.azure.com/";
        string apiKey = "test_api_key";
        var azureOpenAIClient = new AzureOpenAIClient(new Uri(endpoint), new ApiKeyCredential(apiKey));
        string serviceId = "test_service_id";
        string modelId = "gpt-35-turbo";

        // Act
        builder.AddAzureOpenAIChatClient(deploymentName, azureOpenAIClient, serviceId, modelId);

        // Assert
        var kernel = builder.Build();
        Assert.NotNull(kernel.GetRequiredService<IChatClient>());
        Assert.NotNull(kernel.GetRequiredService<IChatClient>(serviceId));
    }
}
