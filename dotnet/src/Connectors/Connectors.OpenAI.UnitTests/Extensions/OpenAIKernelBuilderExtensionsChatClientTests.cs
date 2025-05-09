// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Extensions;

public class OpenAIKernelBuilderExtensionsChatClientTests
{
    [Fact]
    public void AddOpenAIChatClientNullArgsThrow()
    {
        // Arrange
        IKernelBuilder builder = null!;
        string modelId = "gpt-3.5-turbo";
        string apiKey = "test_api_key";
        string orgId = "test_org_id";
        string serviceId = "test_service_id";

        // Act & Assert
        var exception = Assert.Throws<ArgumentNullException>(() => builder.AddOpenAIChatClient(modelId, apiKey, orgId, serviceId));
        Assert.Equal("builder", exception.ParamName);

        exception = Assert.Throws<ArgumentNullException>(() => builder.AddOpenAIChatClient(modelId, new OpenAIClient(apiKey), serviceId));
        Assert.Equal("builder", exception.ParamName);

        using var httpClient = new HttpClient();
        exception = Assert.Throws<ArgumentNullException>(() => builder.AddOpenAIChatClient(modelId, new Uri("http://localhost"), apiKey, orgId, serviceId, httpClient));
        Assert.Equal("builder", exception.ParamName);
    }

    [Fact]
    public void AddOpenAIChatClientDefaultValidParametersRegistersService()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();
        string modelId = "gpt-3.5-turbo";
        string apiKey = "test_api_key";
        string orgId = "test_org_id";
        string serviceId = "test_service_id";

        // Act
        builder.AddOpenAIChatClient(modelId, apiKey, orgId, serviceId);

        // Assert
        var kernel = builder.Build();
        Assert.NotNull(kernel.GetRequiredService<IChatClient>());
        Assert.NotNull(kernel.GetRequiredService<IChatClient>(serviceId));
    }

    [Fact]
    public void AddOpenAIChatClientOpenAIClientValidParametersRegistersService()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();
        string modelId = "gpt-3.5-turbo";
        var openAIClient = new OpenAIClient("test_api_key");
        string serviceId = "test_service_id";

        // Act
        builder.AddOpenAIChatClient(modelId, openAIClient, serviceId);

        // Assert
        var kernel = builder.Build();
        Assert.NotNull(kernel.GetRequiredService<IChatClient>());
        Assert.NotNull(kernel.GetRequiredService<IChatClient>(serviceId));
    }

    [Fact]
    public void AddOpenAIChatClientCustomEndpointValidParametersRegistersService()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();
        string modelId = "gpt-3.5-turbo";
        string apiKey = "test_api_key";
        string orgId = "test_org_id";
        string serviceId = "test_service_id";
        using var httpClient = new HttpClient();

        // Act
        builder.AddOpenAIChatClient(modelId, new Uri("http://localhost"), apiKey, orgId, serviceId, httpClient);

        // Assert
        var kernel = builder.Build();
        Assert.NotNull(kernel.GetRequiredService<IChatClient>());
        Assert.NotNull(kernel.GetRequiredService<IChatClient>(serviceId));
    }
}
