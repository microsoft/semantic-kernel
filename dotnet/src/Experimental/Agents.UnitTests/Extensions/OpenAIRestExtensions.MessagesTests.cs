// Copyright (c) Microsoft. All rights reserved.

using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Agents;
using Microsoft.SemanticKernel.Experimental.Agents.Internal;
using Moq;
using Moq.Protected;
using Xunit;

namespace SemanticKernel.Experimental.Agents.UnitTests;

[Trait("Category", "Unit Tests")]
[Trait("Feature", "Agent")]
public sealed class OpenAIRestExtensionsMessagesTests
{
    private const string BogusEndpoint = "http://localhost";
    private const string BogusApiKey = "bogus";
    private const string TestThreadId = "threadId";
    private const string TestMessageId = "msgId";
    private const string TestContent = "Blah blah";

    private readonly OpenAIRestContext _restContext;
    private readonly Mock<HttpMessageHandler> _mockHttpMessageHandler = new();

    public OpenAIRestExtensionsMessagesTests()
    {
        this._mockHttpMessageHandler
            .Protected()
            .Setup<Task<HttpResponseMessage>>("SendAsync", ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(() => new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent("{}") });
        this._restContext = new(BogusEndpoint, BogusApiKey, () => new HttpClient(this._mockHttpMessageHandler.Object));
    }

    [Fact]
    public async Task CreateMessageModelAsync()
    {
        await this._restContext.CreateUserTextMessageAsync(TestThreadId, TestContent).ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Post, 1, this._restContext.GetMessagesUrl(TestThreadId));
    }

    [Fact]
    public async Task GetMessageModelAsync()
    {
        await this._restContext.GetMessageAsync(TestThreadId, TestMessageId).ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Get, 1, this._restContext.GetMessagesUrl(TestThreadId, TestMessageId));
    }

    [Fact]
    public async Task GetMessageModelsAsync()
    {
        await this._restContext.GetMessagesAsync(TestThreadId).ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Get, 1, this._restContext.GetMessagesUrl(TestThreadId));
    }

    [Fact]
    public async Task GetSpecificMessageModelsAsync()
    {
        var messageIDs = new string[] { "1", "2", "3" };

        await this._restContext.GetMessagesAsync(TestThreadId, messageIDs).ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Get, messageIDs.Length);
    }
}
