// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.HuggingFace.TextGeneration;

/// <summary>
/// Integration tests for <see cref="HuggingFaceTextGenerationService"/>.
/// </summary>
public sealed class HuggingFaceTextGenerationTests(ITestOutputHelper output) : HuggingFaceTestsBase(output)
{
    private const string Input = "This is test";

    [Fact(Skip = "This test is for manual verification.")]
    public async Task HuggingFaceRemoteTextGenerationAsync()
    {
        // Arrange
        var huggingFaceRemote = this.CreateTextGenerationService();

        // Act
        var remoteResponse = await huggingFaceRemote.GetTextContentAsync(Input, new HuggingFacePromptExecutionSettings() { MaxNewTokens = 50 });

        // Assert
        Assert.NotNull(remoteResponse.Text);
        Assert.StartsWith(Input, remoteResponse.Text, StringComparison.Ordinal);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task HuggingFaceLocalTextGenerationAsync()
    {
        // Arrange
        var huggingFaceLocal = this.CreateTextGenerationService(new Uri(this.Config.TextGenerationEndpoint));

        // Act
        var localResponse = await huggingFaceLocal.GetTextContentAsync(Input, new HuggingFacePromptExecutionSettings() { MaxNewTokens = 50 });

        // Assert
        Assert.NotNull(localResponse.Text);
        Assert.StartsWith(Input, localResponse.Text, StringComparison.Ordinal);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task RemoteHuggingFaceTextGenerationWithCustomHttpClientAsync()
    {
        // Arrange
        using var httpClient = new HttpClient();
        httpClient.BaseAddress = new Uri(this.Config.TextGenerationEndpoint);
        var huggingFaceRemote = this.CreateTextGenerationService(httpClient: httpClient);

        // Act
        var remoteResponse = await huggingFaceRemote.GetTextContentAsync(Input, new HuggingFacePromptExecutionSettings() { MaxNewTokens = 50 });

        // Assert
        Assert.NotNull(remoteResponse.Text);
        Assert.StartsWith(Input, remoteResponse.Text, StringComparison.Ordinal);
    }
}
