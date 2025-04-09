// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.AI.Inference;
using Azure.Core;
using Azure.Core.Pipeline;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Connectors.AzureAIInference.Core;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.AzureAIInference.UnitTests.Core;

public sealed class ChatClientCoreTests
{
    private readonly Uri _endpoint = new("http://localhost");

    [Fact]
    public void ItCanBeInstantiatedAndPropertiesSetAsExpected()
    {
        // Arrange
        var logger = new Mock<ILogger<ChatClientCoreTests>>().Object;
        var breakingGlassClient = new ChatCompletionsClient(this._endpoint, new AzureKeyCredential("key"));

        // Act
        var clientCoreModelConstructor = new ChatClientCore("model1", "apiKey", this._endpoint);
        var clientCoreBreakingGlassConstructor = new ChatClientCore("model1", breakingGlassClient, logger: logger);

        // Assert
        Assert.Equal("model1", clientCoreModelConstructor.ModelId);
        Assert.Equal("model1", clientCoreBreakingGlassConstructor.ModelId);

        Assert.NotNull(clientCoreModelConstructor.Client);
        Assert.NotNull(clientCoreBreakingGlassConstructor.Client);
        Assert.Equal(breakingGlassClient, clientCoreBreakingGlassConstructor.Client);
        Assert.Equal(NullLogger.Instance, clientCoreModelConstructor.Logger);
        Assert.Equal(logger, clientCoreBreakingGlassConstructor.Logger);
    }

    [Theory]
    [InlineData("http://localhost", null)]
    [InlineData(null, "http://localhost")]
    [InlineData("http://localhost-1", "http://localhost-2")]
    public void ItUsesEndpointAsExpected(string? clientBaseAddress, string? providedEndpoint)
    {
        // Arrange
        Uri? endpoint = null;
        HttpClient? client = null;
        if (providedEndpoint is not null)
        {
            endpoint = new Uri(providedEndpoint);
        }

        if (clientBaseAddress is not null)
        {
            client = new HttpClient { BaseAddress = new Uri(clientBaseAddress) };
        }

        // Act
        var clientCore = new ChatClientCore("model", "apiKey", endpoint: endpoint, httpClient: client);

        // Assert
        Assert.Equal(endpoint ?? client?.BaseAddress ?? new Uri("https://api.openai.com/v1"), clientCore.Endpoint);

        Assert.True(clientCore.Attributes.ContainsKey(AIServiceExtensions.EndpointKey));
        Assert.Equal(endpoint?.ToString() ?? client?.BaseAddress?.ToString(), clientCore.Attributes[AIServiceExtensions.EndpointKey]);

        client?.Dispose();
    }

    [Fact]
    public void ItThrowsIfNoEndpointOptionIsProvided()
    {
        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new ChatClientCore("model", "apiKey", endpoint: null, httpClient: null));
    }

    [Fact]
    public async Task ItAddSemanticKernelHeadersOnEachRequestAsync()
    {
        // Arrange
        using HttpMessageHandlerStub handler = new();
        using HttpClient httpClient = new(handler);
        httpClient.BaseAddress = this._endpoint;
        handler.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK);

        var clientCore = new ChatClientCore(modelId: "model", apiKey: "test", httpClient: httpClient);

        var pipelineMessage = clientCore.Client!.Pipeline.CreateMessage();
        pipelineMessage.Request.Method = RequestMethod.Post;
        pipelineMessage.Request.Uri = new RequestUriBuilder() { Host = "localhost", Scheme = "https" };
        pipelineMessage.Request.Content = RequestContent.Create(new BinaryData("test"));

        // Act
        await clientCore.Client.Pipeline.SendAsync(pipelineMessage, CancellationToken.None);

        // Assert
        Assert.True(handler.RequestHeaders!.Contains(HttpHeaderConstant.Names.SemanticKernelVersion));
        Assert.Equal(HttpHeaderConstant.Values.GetAssemblyVersion(typeof(ChatClientCore)), handler.RequestHeaders.GetValues(HttpHeaderConstant.Names.SemanticKernelVersion).FirstOrDefault());

        Assert.True(handler.RequestHeaders.Contains("User-Agent"));
        Assert.Contains(HttpHeaderConstant.Values.UserAgent, handler.RequestHeaders.GetValues("User-Agent").FirstOrDefault());
    }

    [Fact]
    public async Task ItDoesNotAddSemanticKernelHeadersWhenBreakingGlassClientIsProvidedAsync()
    {
        // Arrange
        using HttpMessageHandlerStub handler = new();
        using HttpClient httpClient = new(handler);
        handler.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK);

        var clientCore = new ChatClientCore(
            modelId: "model",
            chatClient: new ChatCompletionsClient(this._endpoint, new AzureKeyCredential("api-key"),
                new AzureAIInferenceClientOptions()
                {
                    Transport = new HttpClientTransport(httpClient),
                    RetryPolicy = new RetryPolicy(maxRetries: 0), // Disable Azure SDK retry policy if and only if a custom HttpClient is provided.
                    Retry = { NetworkTimeout = Timeout.InfiniteTimeSpan } // Disable Azure SDK default timeout
                }));

        var pipelineMessage = clientCore.Client!.Pipeline.CreateMessage();
        pipelineMessage.Request.Method = RequestMethod.Post;
        pipelineMessage.Request.Uri = new RequestUriBuilder { Scheme = "http", Host = "http://localhost" };
        pipelineMessage.Request.Content = RequestContent.Create(new BinaryData("test"));

        // Act
        await clientCore.Client.Pipeline.SendAsync(pipelineMessage, CancellationToken.None);

        // Assert
        Assert.False(handler.RequestHeaders!.Contains(HttpHeaderConstant.Names.SemanticKernelVersion));
        Assert.DoesNotContain(HttpHeaderConstant.Values.UserAgent, handler.RequestHeaders.GetValues("User-Agent").FirstOrDefault());
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("value")]
    public void ItAddsAttributesButDoesNothingIfNullOrEmpty(string? value)
    {
        // Arrange
        var clientCore = new ChatClientCore("model", "api-key", this._endpoint);

        // Act
        clientCore.AddAttribute("key", value);

        // Assert
        if (string.IsNullOrEmpty(value))
        {
            Assert.False(clientCore.Attributes.ContainsKey("key"));
        }
        else
        {
            Assert.True(clientCore.Attributes.ContainsKey("key"));
            Assert.Equal(value, clientCore.Attributes["key"]);
        }
    }

    [Fact]
    public void ItAddsModelIdAttributeAsExpected()
    {
        // Arrange
        var expectedModelId = "modelId";

        // Act
        var clientCore = new ChatClientCore(expectedModelId, "api-key", this._endpoint);
        var clientCoreBreakingGlass = new ChatClientCore(expectedModelId, new ChatCompletionsClient(this._endpoint, new AzureKeyCredential(" ")));

        // Assert
        Assert.True(clientCore.Attributes.ContainsKey(AIServiceExtensions.ModelIdKey));
        Assert.True(clientCoreBreakingGlass.Attributes.ContainsKey(AIServiceExtensions.ModelIdKey));
        Assert.Equal(expectedModelId, clientCore.Attributes[AIServiceExtensions.ModelIdKey]);
        Assert.Equal(expectedModelId, clientCoreBreakingGlass.Attributes[AIServiceExtensions.ModelIdKey]);
    }
}
