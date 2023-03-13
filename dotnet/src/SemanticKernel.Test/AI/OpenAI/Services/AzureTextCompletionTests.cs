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
public class AzureTextCompletionTests
{
    private readonly Mock<IAzureOpenAIServiceClient> _mockServiceClient;
    private readonly Mock<IAzureOpenAIDeploymentProvider> _mockDeploymentProvider;
    private readonly AzureTextCompletion _sut;
    private readonly IList<Choice> _completions;

    public AzureTextCompletionTests()
    {
        this._completions = new List<Choice>();
        this._completions.Add(new Choice { Index = 0, Text = "first-fake-completion-text" });
        this._completions.Add(new Choice { Index = 1, Text = "second-fake-completion-text" });

        var completionResponse = new CompletionResponse { Completions = this._completions };

        this._mockServiceClient = new Mock<IAzureOpenAIServiceClient>();
        this._mockServiceClient
            .Setup(sc => sc.ExecuteCompletionAsync(It.IsAny<AzureCompletionRequest>(), It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(completionResponse);

        this._mockDeploymentProvider = new Mock<IAzureOpenAIDeploymentProvider>();
        this._mockDeploymentProvider
            .Setup(p => p.GetDeploymentNameAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync("fake-deployment-name");

        this._sut = new AzureTextCompletion(this._mockServiceClient.Object, this._mockDeploymentProvider.Object, "fake-model-id");
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
    public async Task ItDelegatesDeploymentNameRetrievalToDeploymentProviderAsync()
    {
        //Arrange
        var requestSettings = new CompleteRequestSettings();

        //Act
        await this._sut.CompleteAsync("fake-prompt", requestSettings, CancellationToken.None);

        //Assert
        this._mockDeploymentProvider.Verify(p => p.GetDeploymentNameAsync("fake-model-id", It.IsAny<CancellationToken>()));
    }

    [Fact]
    public async Task ItDelegatesCompleationToServiceClientAsync()
    {
        //Arrange
        var requestSettings = new CompleteRequestSettings();

        //Act
        await this._sut.CompleteAsync("fake-prompt", requestSettings, CancellationToken.None);

        //Assert
        this._mockServiceClient.Verify(sc => sc.ExecuteCompletionAsync(It.IsAny<AzureCompletionRequest>(), It.IsAny<string>(), It.IsAny<CancellationToken>()));
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

