// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.HuggingFace.TextCompletion;
using Xunit;

namespace SemanticKernel.Connectors.HuggingFace.IntegrationTests;

/// <summary>
/// Integration tests for <see cref="HuggingFaceTextCompletion"/>.
/// </summary>
public sealed class HuggingFaceTextCompletionTests
{
    private const string BaseUri = "http://localhost:5000";
    private const string Model = "gpt2";

    [Fact(Skip = "This test is for manual verification.")]
    public async Task HuggingFaceLocalAndRemoteTextCompletionAsync()
    {
        // Arrange
        const string input = "This is test";

        using var huggingFaceLocal = new HuggingFaceTextCompletion(new Uri(BaseUri), Model);
        using var huggingFaceRemote = new HuggingFaceTextCompletion(this.GetApiKey(), Model);

        // Act
        var localResponse = await huggingFaceLocal.CompleteAsync(input, new CompleteRequestSettings()).ConfigureAwait(false);
        var remoteResponse = await huggingFaceRemote.CompleteAsync(input, new CompleteRequestSettings()).ConfigureAwait(false);

        // Assert
        Assert.NotNull(localResponse);
        Assert.NotNull(remoteResponse);

        Assert.StartsWith(input, localResponse, StringComparison.InvariantCulture);
        Assert.StartsWith(input, remoteResponse, StringComparison.InvariantCulture);
    }

    private string GetApiKey()
    {
        return Environment.GetEnvironmentVariable("HF_API_KEY")!;
    }
}
