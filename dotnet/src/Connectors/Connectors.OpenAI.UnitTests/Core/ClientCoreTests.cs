// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.ClientModel.Primitives;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;
using Moq;
using OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Core;
public partial class ClientCoreTests
{
    [Fact]
    public void ItCanBeInstantiatedAndPropertiesSetAsExpected()
    {
        // Act
        var logger = new Mock<ILogger<ClientCoreTests>>().Object;
        var openAIClient = new OpenAIClient(new ApiKeyCredential("key"));

        var clientCoreModelConstructor = new ClientCore("model1", "apiKey");
        var clientCoreOpenAIClientConstructor = new ClientCore("model1", openAIClient, logger: logger);

        // Assert
        Assert.NotNull(clientCoreModelConstructor);
        Assert.NotNull(clientCoreOpenAIClientConstructor);

        Assert.Equal("model1", clientCoreModelConstructor.ModelId);
        Assert.Equal("model1", clientCoreOpenAIClientConstructor.ModelId);

        Assert.NotNull(clientCoreModelConstructor.Client);
        Assert.NotNull(clientCoreOpenAIClientConstructor.Client);
        Assert.Equal(openAIClient, clientCoreOpenAIClientConstructor.Client);
        Assert.Equal(NullLogger.Instance, clientCoreModelConstructor.Logger);
        Assert.Equal(logger, clientCoreOpenAIClientConstructor.Logger);
    }

    [Theory]
    [InlineData(null, null)]
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
        var clientCore = new ClientCore("model", "apiKey", endpoint: endpoint, httpClient: client);

        // Assert
        Assert.Equal(endpoint ?? client?.BaseAddress ?? new Uri("https://api.openai.com/v1"), clientCore.Endpoint);
        Assert.True(clientCore.Attributes.ContainsKey(AIServiceExtensions.EndpointKey));
        Assert.Equal(endpoint?.ToString() ?? client?.BaseAddress?.ToString() ?? "https://api.openai.com/v1", clientCore.Attributes[AIServiceExtensions.EndpointKey]);

        client?.Dispose();
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItAddOrganizationHeaderWhenProvidedAsync(bool organizationIdProvided)
    {
        using HttpMessageHandlerStub handler = new();
        using HttpClient client = new(handler);
        handler.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK);

        // Act
        var clientCore = new ClientCore(
            modelId: "model",
            apiKey: "test",
            organizationId: (organizationIdProvided) ? "organization" : null,
            httpClient: client);

        var pipelineMessage = clientCore.Client!.Pipeline.CreateMessage();
        pipelineMessage.Request.Method = "POST";
        pipelineMessage.Request.Uri = new Uri("http://localhost");
        pipelineMessage.Request.Content = BinaryContent.Create(new BinaryData("test"));

        // Assert
        await clientCore.Client.Pipeline.SendAsync(pipelineMessage);

        if (organizationIdProvided)
        {
            Assert.True(handler.RequestHeaders!.Contains("OpenAI-Organization"));
            Assert.Equal("organization", handler.RequestHeaders.GetValues("OpenAI-Organization").FirstOrDefault());
        }
        else
        {
            Assert.False(handler.RequestHeaders!.Contains("OpenAI-Organization"));
        }
    }

    [Fact]
    public async Task ItAddSemanticKernelHeadersOnEachRequestAsync()
    {
        using HttpMessageHandlerStub handler = new();
        using HttpClient client = new(handler);
        handler.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK);

        // Act
        var clientCore = new ClientCore(modelId: "model", apiKey: "test", httpClient: client);

        var pipelineMessage = clientCore.Client!.Pipeline.CreateMessage();
        pipelineMessage.Request.Method = "POST";
        pipelineMessage.Request.Uri = new Uri("http://localhost");
        pipelineMessage.Request.Content = BinaryContent.Create(new BinaryData("test"));

        // Assert
        await clientCore.Client.Pipeline.SendAsync(pipelineMessage);

        Assert.True(handler.RequestHeaders!.Contains(HttpHeaderConstant.Names.SemanticKernelVersion));
        Assert.Equal(HttpHeaderConstant.Values.GetAssemblyVersion(typeof(ClientCore)), handler.RequestHeaders.GetValues(HttpHeaderConstant.Names.SemanticKernelVersion).FirstOrDefault());

        Assert.True(handler.RequestHeaders.Contains("User-Agent"));
        Assert.Contains(HttpHeaderConstant.Values.UserAgent, handler.RequestHeaders.GetValues("User-Agent").FirstOrDefault());
    }

    [Fact]
    public async Task ItDoesNotAddSemanticKernelHeadersWhenOpenAIClientIsProvidedAsync()
    {
        using HttpMessageHandlerStub handler = new();
        using HttpClient client = new(handler);
        handler.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK);

        // Act
        var clientCore = new ClientCore(
            modelId: "model",
            openAIClient: new OpenAIClient(
                new ApiKeyCredential("test"),
                new OpenAIClientOptions()
                {
                    Transport = new HttpClientPipelineTransport(client),
                    RetryPolicy = new ClientRetryPolicy(maxRetries: 0),
                    NetworkTimeout = Timeout.InfiniteTimeSpan
                }));

        var pipelineMessage = clientCore.Client!.Pipeline.CreateMessage();
        pipelineMessage.Request.Method = "POST";
        pipelineMessage.Request.Uri = new Uri("http://localhost");
        pipelineMessage.Request.Content = BinaryContent.Create(new BinaryData("test"));

        // Assert
        await clientCore.Client.Pipeline.SendAsync(pipelineMessage);

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
        var clientCore = new ClientCore("model", "apikey");
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
        var clientCore = new ClientCore(expectedModelId, "apikey");
        var clientCoreBreakingGlass = new ClientCore(expectedModelId, new OpenAIClient(new ApiKeyCredential(" ")));

        // Assert
        Assert.True(clientCore.Attributes.ContainsKey(AIServiceExtensions.ModelIdKey));
        Assert.True(clientCoreBreakingGlass.Attributes.ContainsKey(AIServiceExtensions.ModelIdKey));
        Assert.Equal(expectedModelId, clientCore.Attributes[AIServiceExtensions.ModelIdKey]);
        Assert.Equal(expectedModelId, clientCoreBreakingGlass.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void ItAddOrNotOrganizationIdAttributeWhenProvided()
    {
        // Arrange
        var expectedOrganizationId = "organizationId";

        // Act
        var clientCore = new ClientCore("modelId", "apikey", expectedOrganizationId);
        var clientCoreWithoutOrgId = new ClientCore("modelId", "apikey");

        // Assert
        Assert.True(clientCore.Attributes.ContainsKey(ClientCore.OrganizationKey));
        Assert.Equal(expectedOrganizationId, clientCore.Attributes[ClientCore.OrganizationKey]);
        Assert.False(clientCoreWithoutOrgId.Attributes.ContainsKey(ClientCore.OrganizationKey));
    }

    [Fact]
    public void ItThrowsWhenNotUsingCustomEndpointAndApiKeyIsNotProvided()
    {
        // Act & Assert
        Assert.Throws<ArgumentException>(() => new ClientCore("modelId", " "));
        Assert.Throws<ArgumentException>(() => new ClientCore("modelId", ""));
        Assert.Throws<ArgumentNullException>(() => new ClientCore("modelId", apiKey: null!));
    }

    [Fact]
    public void ItDoesNotThrowWhenUsingCustomEndpointAndApiKeyIsNotProvided()
    {
        // Act & Assert
        ClientCore? clientCore = null;
        clientCore = new ClientCore("modelId", " ", endpoint: new Uri("http://localhost"));
        clientCore = new ClientCore("modelId", "", endpoint: new Uri("http://localhost"));
        clientCore = new ClientCore("modelId", apiKey: null!, endpoint: new Uri("http://localhost"));
    }
}
