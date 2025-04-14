// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel.Primitives;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.Core;

public sealed class ClientCoreTests : IDisposable
{
    private readonly MultipleHttpMessageHandlerStub _multiHttpMessageHandlerStub;
    private readonly HttpClient _httpClient;

    public ClientCoreTests()
    {
        this._multiHttpMessageHandlerStub = new MultipleHttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._multiHttpMessageHandlerStub);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._multiHttpMessageHandlerStub.Dispose();
    }

    [Fact]
    public async Task AuthenticationHeaderShouldBeProvidedOnlyOnce()
    {
        // Arrange
        using var firstResponse = new HttpResponseMessage(System.Net.HttpStatusCode.TooManyRequests);
        using var secondResponse = new HttpResponseMessage(System.Net.HttpStatusCode.TooManyRequests);
        using var thirdResponse = new HttpResponseMessage(System.Net.HttpStatusCode.TooManyRequests);

        this._multiHttpMessageHandlerStub.ResponsesToReturn.AddRange([firstResponse, secondResponse, thirdResponse]);
        var options = new AzureOpenAIClientOptions()
        {
            Transport = new HttpClientPipelineTransport(this._httpClient),
            RetryPolicy = new ClientRetryPolicy(2),
            NetworkTimeout = TimeSpan.FromSeconds(10),
        };

        var azureClient = new AzureOpenAIClient(
            endpoint: new Uri("http://any"),
            credential: new TestJWTBearerTokenCredential(),
            options: options);

        var clientCore = new AzureClientCore("deployment-name", azureClient);

        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("User test");

        // Act
        var exception = await Record.ExceptionAsync(() => clientCore.GetChatMessageContentsAsync("model-id", chatHistory, null, null, CancellationToken.None));

        // Assert
        Assert.NotNull(exception);
        Assert.Equal(3, this._multiHttpMessageHandlerStub.RequestHeaders.Count);

        foreach (var requestHeaders in this._multiHttpMessageHandlerStub.RequestHeaders)
        {
            this._multiHttpMessageHandlerStub.RequestHeaders[2]!.TryGetValues("Authorization", out var authHeaders);
            Assert.NotNull(authHeaders);
            Assert.Single(authHeaders);
        }
    }

    private sealed class TestJWTBearerTokenCredential : TokenCredential
    {
        public override AccessToken GetToken(TokenRequestContext requestContext, CancellationToken cancellationToken)
        {
            return new AccessToken("JWT", DateTimeOffset.Now.AddHours(1));
        }

        public override ValueTask<AccessToken> GetTokenAsync(TokenRequestContext requestContext, CancellationToken cancellationToken)
        {
            return ValueTask.FromResult(new AccessToken("JWT", DateTimeOffset.Now.AddHours(1)));
        }
    }
}
