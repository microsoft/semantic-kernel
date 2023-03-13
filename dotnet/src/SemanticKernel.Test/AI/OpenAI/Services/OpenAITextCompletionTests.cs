// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.OpenAI.Clients;
using Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;
using Microsoft.SemanticKernel.AI.OpenAI.Services;
using Microsoft.SemanticKernel.AI.OpenAI.Services.Deployments;
using Moq;
using Xunit;
using static Microsoft.SemanticKernel.AI.OpenAI.HttpSchema.CompletionResponse;

namespace SemanticKernelTests.AI.OpenAI.Services;
public class OpenAITextCompletionTests
{
    private readonly Mock<IOpenAIServiceClient> _mockServiceClient;
    private readonly OpenAITextCompletion _sut;
    private readonly IList<Choice> _completions;

    public OpenAITextCompletionTests()
    {
        this._completions = new List<Choice>();
        this._completions.Add(new Choice { Index = 0, Text = "first-fake-completion-text" });
        this._completions.Add(new Choice { Index = 1, Text = "second-fake-completion-text" });

        var completionResponse = new CompletionResponse { Completions = this._completions };

        this._mockServiceClient = new Mock<IOpenAIServiceClient>();
        this._mockServiceClient
            .Setup(sc => sc.ExecuteCompletionAsync(It.IsAny<OpenAICompletionRequest>(), It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(completionResponse);

        this._sut = new OpenAITextCompletion(this._mockServiceClient.Object, "fake-model-id");
    }

    [Fact]
    public async Task ItThrowExceptionForInvalidTokenNumberAsync()
    {
        //Arrange
        var requestSettings = new CompleteRequestSettings
        {
            MaxTokens = 0
        };

        //Act & Assert
        await Assert.ThrowsAsync<AIException>(async () => await this._sut.CompleteAsync("fake-prompt", requestSettings, CancellationToken.None));
    }

    [Fact]
    public async Task ItDelegatesCompleationToServiceClientAsync()
    {
        //Arrange
        var requestSettings = new CompleteRequestSettings();

        //Act
        await this._sut.CompleteAsync("fake-prompt", requestSettings, CancellationToken.None);

        //Assert
        this._mockServiceClient.Verify(sc => sc.ExecuteCompletionAsync(It.IsAny<OpenAICompletionRequest>(), It.IsAny<string>(), It.IsAny<CancellationToken>()));
    }

    [Fact]
    public async Task ItReturnsTextOfFirstCompletionAsync()
    {
        //Arrange
        var requestSettings = new CompleteRequestSettings();

        //Act
        var result = await this._sut.CompleteAsync("fake-prompt", requestSettings, CancellationToken.None);

        //Assert
        Assert.Equal("first-fake-completion-text", result);
    }
}

