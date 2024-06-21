// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.ClientModel.Primitives;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Http;
using OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Core;
public class ClientCoreTests
{
    [Fact]
    public void ItCanBeInstantiated()
    {
        // Act
        var openAIClient = new OpenAIClient(new ApiKeyCredential("key"));

        var clientCoreModelConstructor = new ClientCore("model1", "apiKey");
        var clientCoreOpenAIClientConstructor = new ClientCore("model1", openAIClient);

        // Assert
        Assert.NotNull(clientCoreModelConstructor);
        Assert.NotNull(clientCoreOpenAIClientConstructor);

        Assert.Equal("model1", clientCoreModelConstructor.ModelId);
        Assert.Equal("model1", clientCoreOpenAIClientConstructor.ModelId);

        Assert.NotNull(clientCoreModelConstructor.Client);
        Assert.NotNull(clientCoreOpenAIClientConstructor.Client);
        Assert.Equal(openAIClient, clientCoreOpenAIClientConstructor.Client);
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

        var pipelineMessage = clientCore.Client.Pipeline.CreateMessage();
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

    [Theory]
    [InlineData(true, Skip = "Semantic Kernel header is not provided when using specific OpenAI client")]
    [InlineData(false)]
    public async Task ItAddSemanticKernelHeadersOnEachRequestAsync(bool useOpenAIClient)
    {
        using HttpMessageHandlerStub handler = new();
        using HttpClient client = new(handler);
        handler.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK);

        // Act
        var clientCore = (!useOpenAIClient)
            ? new ClientCore(modelId: "model", apiKey: "test", httpClient: client)
            : new ClientCore(modelId: "model", openAIClient: new OpenAIClient(
                new ApiKeyCredential("test"),
                new OpenAIClientOptions()
                {
                    Transport = new HttpClientPipelineTransport(client),
                    RetryPolicy = new ClientRetryPolicy(maxRetries: 0),
                    NetworkTimeout = Timeout.InfiniteTimeSpan
                }));

        var pipelineMessage = clientCore.Client.Pipeline.CreateMessage();
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
}
