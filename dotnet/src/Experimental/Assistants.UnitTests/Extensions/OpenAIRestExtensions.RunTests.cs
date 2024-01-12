// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants;
using Microsoft.SemanticKernel.Experimental.Assistants.Internal;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;
using Moq;
using Moq.Protected;
using Xunit;

namespace SemanticKernel.Experimental.Assistants.UnitTests;

[Trait("Category", "Unit Tests")]
[Trait("Feature", "Assistant")]
public sealed class OpenAIRestExtensionsRunTests
{
    private const string BogusApiKey = "bogus";
    private const string TestAssistantId = "assistantId";
    private const string TestThreadId = "threadId";
    private const string TestRunId = "runId";

    private readonly OpenAIRestContext _restContext;
    private readonly Mock<HttpMessageHandler> _mockHttpMessageHandler = new();

    public OpenAIRestExtensionsRunTests()
    {
        this._mockHttpMessageHandler
            .Protected()
            .Setup<Task<HttpResponseMessage>>("SendAsync", ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(() => new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent("{}") });
        this._restContext = new(BogusApiKey, () => new HttpClient(this._mockHttpMessageHandler.Object));
    }

    [Fact]
    public async Task CreateRunAsync()
    {
        await this._restContext.CreateRunAsync(TestThreadId, TestAssistantId).ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Post, 1, OpenAIRestExtensions.GetRunUrl(TestThreadId));
    }

    [Fact]
    public async Task GetRunAsync()
    {
        await this._restContext.GetRunAsync(TestThreadId, TestRunId).ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Get, 1, OpenAIRestExtensions.GetRunUrl(TestThreadId, TestRunId));
    }

    [Fact]
    public async Task GetRunStepsAsync()
    {
        await this._restContext.GetRunStepsAsync(TestThreadId, TestRunId).ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Get, 1, OpenAIRestExtensions.GetRunStepsUrl(TestThreadId, TestRunId));
    }

    [Fact]
    public async Task AddToolOutputsAsync()
    {
        var toolResults = Array.Empty<ToolResultModel>();

        await this._restContext.AddToolOutputsAsync(TestThreadId, TestRunId, toolResults).ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Post, 1, OpenAIRestExtensions.GetRunToolOutput(TestThreadId, TestRunId));
    }
}
