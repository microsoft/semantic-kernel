// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Net.Http;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Core;
public class ClientCoreTests
{
    [Fact]
    public void ItCanBeInstantiated()
    {
        // Act
        var client = new OpenAIClient(new ApiKeyCredential("key"));

        var clientCoreModelConstructor = new ClientCore("model1");
        var clientCoreOpenAIClientConstructor = new ClientCore("model1", client);

        // Assert
        Assert.NotNull(clientCoreModelConstructor);
        Assert.NotNull(clientCoreOpenAIClientConstructor);

        Assert.Equal("model1", clientCoreModelConstructor.ModelId);
        Assert.Equal("model1", clientCoreOpenAIClientConstructor.ModelId);

        Assert.NotNull(clientCoreModelConstructor.Client);
        Assert.NotNull(clientCoreOpenAIClientConstructor.Client);
        Assert.Equal(client, clientCoreOpenAIClientConstructor.Client);
    }


    [Theory]
    [InlineData(null, null)]
    [InlineData("http://localhost", null)]
    [InlineData(null, "http://localhost")]
    [InlineData("http://localhost", "http://localhost")]
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
        var clientCore = new ClientCore("model", endpoint: endpoint, httpClient: client);

        // Assert
        Assert.Equal(endpoint ?? client?.BaseAddress ?? new Uri("https://api.openai.com/v1"), clientCore.Endpoint);

        client?.Dispose();
    }
}
