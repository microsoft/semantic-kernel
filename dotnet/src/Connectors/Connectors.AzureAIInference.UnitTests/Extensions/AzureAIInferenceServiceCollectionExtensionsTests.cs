// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Azure;
using Azure.AI.Inference;
using Azure.Core;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureAIInference.Core;
using Microsoft.SemanticKernel.Http;
using Xunit;

namespace SemanticKernel.Connectors.AzureAIInference.UnitTests.Extensions;

public sealed class AzureAIInferenceServiceCollectionExtensionsTests
{
    private readonly Uri _endpoint = new("https://endpoint");

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.ClientInline)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    public void ItCanAddChatCompletionService(InitializationType type)
    {
        // Arrange
        var client = new ChatCompletionsClient(this._endpoint, new AzureKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton(client);

        // Act
        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAzureAIInferenceChatCompletion("modelId", "api-key", this._endpoint),
            InitializationType.ClientInline => builder.Services.AddAzureAIInferenceChatCompletion("modelId", client),
            InitializationType.ClientInServiceProvider => builder.Services.AddAzureAIInferenceChatCompletion("modelId", chatClient: null),
            _ => builder.Services
        };

        // Assert
        var chatCompletionService = builder.Build().GetRequiredService<IChatCompletionService>();
        Assert.Equal("ChatClientChatCompletionService", chatCompletionService.GetType().Name);
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.ClientInline)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    public void ItCanAddChatClientService(InitializationType type)
    {
        // Arrange
        var client = new ChatCompletionsClient(this._endpoint, new AzureKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton(client);

        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAzureAIInferenceChatClient("modelId", "api-key", this._endpoint),
            InitializationType.ClientInline => builder.Services.AddAzureAIInferenceChatClient("modelId", client),
            InitializationType.ClientInServiceProvider => builder.Services.AddAzureAIInferenceChatClient("modelId", chatClient: null),
            _ => builder.Services
        };

        // Act & Assert
        var sut = builder.Build().GetRequiredService<IChatClient>();
        Assert.NotNull(sut);
        Assert.Equal("KernelFunctionInvokingChatClient", sut.GetType().Name);
    }

    public enum InitializationType
    {
        ApiKey,
        ClientInline,
        ChatClientInline,
        ClientInServiceProvider,
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    public async Task ItAddSemanticKernelHeadersOnEachChatCompletionRequestAsync(InitializationType type)
    {
        // Arrange
        using HttpMessageHandlerStub handler = new();
        using HttpClient httpClient = new(handler);
        httpClient.BaseAddress = this._endpoint;
        handler.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("TestData/chat_completion_response.json"))
        };

        var builder = Kernel.CreateBuilder();

        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAzureAIInferenceChatCompletion("modelId", "api-key", this._endpoint, httpClient: httpClient),
            InitializationType.ClientInServiceProvider => builder.Services.AddAzureAIInferenceChatCompletion(
                modelId: "modelId",
                credential: DelegatedTokenCredential.Create((_, _) => new AccessToken("test", DateTimeOffset.Now)),
                endpoint: this._endpoint,
                httpClient: httpClient),
            _ => builder.Services
        };

        var sut = builder.Build().GetRequiredService<IChatCompletionService>();

        // Act
        await sut.GetChatMessageContentAsync("test");

        // Assert
        Assert.True(handler.RequestHeaders!.Contains(HttpHeaderConstant.Names.SemanticKernelVersion));
        Assert.Equal(HttpHeaderConstant.Values.GetAssemblyVersion(typeof(ChatClientCore)), handler.RequestHeaders.GetValues(HttpHeaderConstant.Names.SemanticKernelVersion).FirstOrDefault());

        Assert.True(handler.RequestHeaders.Contains("User-Agent"));
        Assert.Contains(HttpHeaderConstant.Values.UserAgent, handler.RequestHeaders.GetValues("User-Agent").FirstOrDefault());
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    public async Task ItAddSemanticKernelHeadersOnEachChatClientRequestAsync(InitializationType type)
    {
        // Arrange
        using HttpMessageHandlerStub handler = new();
        using HttpClient httpClient = new(handler);
        httpClient.BaseAddress = this._endpoint;
        handler.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("TestData/chat_completion_response.json"))
        };

        var builder = Kernel.CreateBuilder();

        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAzureAIInferenceChatClient("modelId", "api-key", this._endpoint, httpClient: httpClient),
            InitializationType.ClientInServiceProvider => builder.Services.AddAzureAIInferenceChatClient(
                modelId: "modelId",
                credential: DelegatedTokenCredential.Create((_, _) => new AccessToken("test", DateTimeOffset.Now)),
                endpoint: this._endpoint,
                httpClient: httpClient),
            _ => builder.Services
        };

        var sut = builder.Build().GetRequiredService<IChatClient>();

        // Act
        await sut.GetResponseAsync("test");

        // Assert
        Assert.True(handler.RequestHeaders!.Contains(HttpHeaderConstant.Names.SemanticKernelVersion));
        Assert.Equal(HttpHeaderConstant.Values.GetAssemblyVersion(typeof(ChatClientCore)), handler.RequestHeaders.GetValues(HttpHeaderConstant.Names.SemanticKernelVersion).FirstOrDefault());

        Assert.True(handler.RequestHeaders.Contains("User-Agent"));
        Assert.Contains(HttpHeaderConstant.Values.UserAgent, handler.RequestHeaders.GetValues("User-Agent").FirstOrDefault());
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    public async Task ItAddSemanticKernelHeadersOnEachEmbeddingGeneratorRequestAsync(InitializationType type)
    {
        // Arrange
        using HttpMessageHandlerStub handler = new();
        using HttpClient httpClient = new(handler);
        httpClient.BaseAddress = this._endpoint;
        handler.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("TestData/text-embeddings-response.txt"))
        };

        var builder = Kernel.CreateBuilder();

        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAzureAIInferenceEmbeddingGenerator("modelId", "api-key", this._endpoint, httpClient: httpClient),
            InitializationType.ClientInServiceProvider => builder.Services.AddAzureAIInferenceEmbeddingGenerator(
                modelId: "modelId",
                credential: DelegatedTokenCredential.Create((_, _) => new AccessToken("test", DateTimeOffset.Now)),
                endpoint: this._endpoint,
                httpClient: httpClient),
            _ => builder.Services
        };

        var sut = builder.Build().GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        // Act
        await sut.GenerateAsync("test");

        // Assert
        Assert.True(handler.RequestHeaders!.Contains(HttpHeaderConstant.Names.SemanticKernelVersion));
        Assert.Equal(HttpHeaderConstant.Values.GetAssemblyVersion(typeof(ChatClientCore)), handler.RequestHeaders.GetValues(HttpHeaderConstant.Names.SemanticKernelVersion).FirstOrDefault());

        Assert.True(handler.RequestHeaders.Contains("User-Agent"));
        Assert.Contains(HttpHeaderConstant.Values.UserAgent, handler.RequestHeaders.GetValues("User-Agent").FirstOrDefault());
    }
}
