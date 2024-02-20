// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.CustomClient.Moderation;

public sealed class OpenAIModerationRequestTests
{
    [Fact]
    public void FromTextAndModelIdItReturnsOpenAIModerationRequest()
    {
        // Arrange
        var text = "text-sample";
        var modelId = "modelId-sample";

        // Act
        var result = OpenAIModerationRequest.FromText(text, modelId);

        // Assert
        Assert.Equal(text, result.Input);
        Assert.Equal(modelId, result.Model);
    }
}
