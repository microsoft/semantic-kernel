// Copyright (c) Microsoft. All rights reserved.

using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Agents;
using Microsoft.SemanticKernel.Experimental.Agents.Internal;
using Microsoft.SemanticKernel.Experimental.Agents.Models;
using Moq;
using Moq.Protected;
using Xunit;

namespace SemanticKernel.Experimental.Agents.UnitTests;

[Trait("Category", "Unit Tests")]
[Trait("Feature", "Agent")]
public sealed class OpenAIRestExtensionsAssistantsTests
{
    private const string BogusEndpoint = "http://localhost";
    private const string BogusApiKey = "bogus";
    private const string TestAgentId = "agentId";

    private readonly AssistantModel _assistantModel = new();
    private readonly OpenAIRestContext _restContext;
    private readonly Mock<HttpMessageHandler> _mockHttpMessageHandler = new();

    public OpenAIRestExtensionsAssistantsTests()
    {
        this._mockHttpMessageHandler
            .Protected()
            .Setup<Task<HttpResponseMessage>>("SendAsync", ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(() => new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent("{}") });
        this._restContext = new(BogusEndpoint, BogusApiKey, () => new HttpClient(this._mockHttpMessageHandler.Object));
    }

    [Fact]
    public async Task CreateAssistantModelAsync()
    {
        await this._restContext.CreateAssistantModelAsync(this._assistantModel).ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Post, 1, this._restContext.GetAssistantsUrl());
    }

    [Fact]
    public async Task GetAssistantModelAsync()
    {
        await this._restContext.GetAssistantModelAsync(TestAgentId).ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Get, 1, this._restContext.GetAssistantUrl(TestAgentId));
    }

    [Fact]
    public async Task ListAssistantModelsAsync()
    {
        await this._restContext.ListAssistantModelsAsync(10, false, "20").ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Get, 1, $"{this._restContext.GetAssistantsUrl()}?limit=10&order=desc&after=20");
    }

    [Fact]
    public async Task DeleteAssistantsModelAsync()
    {
        await this._restContext.DeleteAssistantModelAsync(TestAgentId).ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Delete, 1, this._restContext.GetAssistantUrl(TestAgentId));
    }
}
