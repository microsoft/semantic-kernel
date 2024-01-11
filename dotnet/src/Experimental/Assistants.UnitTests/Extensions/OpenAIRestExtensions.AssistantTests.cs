// Copyright (c) Microsoft. All rights reserved.

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
public sealed class OpenAIRestExtensionsAssistantTests
{
    private const string BogusApiKey = "bogus";
    private const string TestAssistantId = "assistantId";

    private readonly AssistantModel _assistantModel = new();
    private readonly OpenAIRestContext _restContext;
    private readonly Mock<HttpMessageHandler> _mockHttpMessageHandler = new();

    public OpenAIRestExtensionsAssistantTests()
    {
        this._mockHttpMessageHandler
            .Protected()
            .Setup<Task<HttpResponseMessage>>("SendAsync", ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(() => new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent("{}") });
        this._restContext = new(BogusApiKey, () => new HttpClient(this._mockHttpMessageHandler.Object));
    }

    [Fact]
    public async Task CreateAssistantModelAsync()
    {
        await this._restContext.CreateAssistantModelAsync(this._assistantModel).ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Post, 1, OpenAIRestExtensions.BaseAssistantUrl);
    }

    [Fact]
    public async Task GetAssistantModelAsync()
    {
        await this._restContext.GetAssistantModelAsync(TestAssistantId).ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Get, 1, OpenAIRestExtensions.GetAssistantUrl(TestAssistantId));
    }

    [Fact]
    public async Task ListAssistantModelsAsync()
    {
        await this._restContext.ListAssistantModelsAsync(10, false, "20").ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Get, 1, $"{OpenAIRestExtensions.BaseAssistantUrl}?limit=10&order=desc&after=20");
    }

    [Fact]
    public async Task DeleteAssistantModelAsync()
    {
        await this._restContext.DeleteAssistantModelAsync(TestAssistantId).ConfigureAwait(true);

        this._mockHttpMessageHandler.VerifyMock(HttpMethod.Delete, 1, OpenAIRestExtensions.GetAssistantUrl(TestAssistantId));
    }
}
