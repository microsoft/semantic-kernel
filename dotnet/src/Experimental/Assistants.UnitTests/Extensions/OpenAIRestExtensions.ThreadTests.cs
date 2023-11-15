// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants.Extensions;
using Microsoft.SemanticKernel.Experimental.Assistants.Internal;
using Moq;
using Moq.Protected;
using Xunit;

namespace SemanticKernel.Experimental.Assistants.UnitTests.Extensions;

[Trait("Category", "Unit Tests")]
public sealed class OpenAIRestExtensionsThreadTests : IDisposable
{
    private const string BogusApiKey = "bogus";
    private const string TestThreadId = "threadId";

    private readonly OpenAIRestContext _restContext;
    private readonly Mock<HttpMessageHandler> _mockHttpMessageHandler = new();
    private readonly HttpResponseMessage _emptyResponse = new()
    {
        StatusCode = HttpStatusCode.OK,
        Content = new StringContent("{}"),
    };

    public OpenAIRestExtensionsThreadTests()
    {
        this._mockHttpMessageHandler
            .Protected()
            .Setup<Task<HttpResponseMessage>>("SendAsync", ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(this._emptyResponse);
        this._restContext = new(BogusApiKey, () => new HttpClient(this._mockHttpMessageHandler.Object));
    }

    [Fact]
    public async Task CreateThreadModelAsync()
    {
        await this._restContext.CreateThreadModelAsync().ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Post, 1,OpenAIRestExtensions.BaseThreadUrl);
    }

    [Fact]
    public async Task GetThreadModelAsync()
    {
        await this._restContext.GetThreadModelAsync(TestThreadId).ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Get, 1, OpenAIRestExtensions.GetThreadUrl(TestThreadId));
    }

    [Fact]
    public async Task DeleteThreadModelAsync()
    {
        await this._restContext.DeleteThreadModelAsync(TestThreadId).ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Delete, 1, OpenAIRestExtensions.GetThreadUrl(TestThreadId));
    }

    public void Dispose()
    {
        this._emptyResponse.Dispose();
    }
}
