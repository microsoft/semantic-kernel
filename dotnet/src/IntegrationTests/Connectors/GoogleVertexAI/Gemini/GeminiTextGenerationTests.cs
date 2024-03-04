// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.TextGeneration;
using xRetry;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.GoogleVertexAI.Gemini;

public sealed class GeminiTextGenerationTests : TestsBase
{
    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task TextGenerationAsync(ServiceType serviceType)
    {
        // Arrange
        const string Input = "Expand this abbreviation: LLM";

        var sut = this.GetTextService(serviceType);

        // Act
        var response = await sut.GetTextContentAsync(Input);

        // Assert
        Assert.NotNull(response.Text);
        this.Output.WriteLine(response.Text);
        Assert.Contains("Large Language Model", response.Text, StringComparison.OrdinalIgnoreCase);
    }

    [RetryTheory]
    [InlineData(ServiceType.GoogleAI, Skip = "This test is for manual verification.")]
    [InlineData(ServiceType.VertexAI, Skip = "This test is for manual verification.")]
    public async Task TextStreamingAsync(ServiceType serviceType)
    {
        // Arrange
        const string Input = "Write a story about a magic backpack.";

        var sut = this.GetTextService(serviceType);

        // Act
        var response = await sut.GetStreamingTextContentsAsync(Input).ToListAsync();

        // Assert
        Assert.NotEmpty(response);
        Assert.True(response.Count > 1);
        var text = string.Concat(response.Select(r => r.Text));
        this.Output.WriteLine(text);
        Assert.False(string.IsNullOrWhiteSpace(text));
    }

    public GeminiTextGenerationTests(ITestOutputHelper output) : base(output) { }
}
