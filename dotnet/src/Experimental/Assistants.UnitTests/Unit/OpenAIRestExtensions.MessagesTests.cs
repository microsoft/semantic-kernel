// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Net;
using System.Threading.Tasks;
using System.Threading;
using Microsoft.SemanticKernel.Experimental.Assistants.Extensions;
using Microsoft.SemanticKernel.Experimental.Assistants.Internal;
using Moq;
using Moq.Protected;
using Xunit;
using System;

namespace SemanticKernel.Experimental.Assistants.UnitTests.Unit;

[Trait("Category", "Unit Tests")]
public sealed class OpenAIRestExtensionsMessagesTests : IDisposable
{
    private const string BogusApiKey = "bogus";
    private const string TestThreadId = "threadId";
    private const string TestMessageId = "msgId";
    private const string TestContent = "Blah blah";

    private readonly OpenAIRestContext _restContext;
    private readonly Mock<HttpMessageHandler> _mockHttpMessageHandler = new();
    private readonly HttpResponseMessage _emptyResponse = new()
    {
        StatusCode = HttpStatusCode.OK,
        Content = new StringContent("{}"),
    };

    public OpenAIRestExtensionsMessagesTests()
    {
        this._mockHttpMessageHandler
            .Protected()
            .Setup<Task<HttpResponseMessage>>("SendAsync", ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(this._emptyResponse);
        this._restContext = new(BogusApiKey, () => new HttpClient(this._mockHttpMessageHandler.Object));
    }

    [Fact]
    public async Task CreateMessageModelAsync()
    {
        await this._restContext.CreateUserTextMessageAsync(TestThreadId, TestContent).ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Post, 1, OpenAIRestExtensions.GetMessagesUrl(TestThreadId));
    }

    [Fact]
    public async Task GetMessageModelAsync()
    {
        await this._restContext.GetMessageAsync(TestThreadId, TestMessageId).ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Get, 1, OpenAIRestExtensions.GetMessagesUrl(TestThreadId, TestMessageId));
    }

    [Fact]
    public async Task GetMessageModelsAsync()
    {
        await this._restContext.GetMessagesAsync(TestThreadId).ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Get, 1, OpenAIRestExtensions.GetMessagesUrl(TestThreadId));
    }

    /* TODO: Need to find a way around disposal of StringContent
    [Fact]
    public async Task GetSpecificMessageModelsAsync()
    {
        var messageIDs = new string[] { "1", "2", "3" };

        await this._restContext.GetMessagesAsync(BogusThreadId, messageIDs).ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Get, messageIDs.Length);
    }*/

    public void Dispose()
    {
        this._emptyResponse.Dispose();
    }
}
