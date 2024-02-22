// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.CustomClient.Moderation;

public sealed class OpenAIModerationRequestTests
{
    [Fact]
    public void FromTextAndModelIdItReturnsOpenAIModerationRequest()
    {
        // Arrange
        List<string> texts = ["killing people", "something illegal", "normal text"];
        var modelId = "modelId-sample";

        // Act
        var result = OpenAIModerationRequest.FromTexts(texts, modelId);

        // Assert
        Assert.Equal(texts, result.Input);
        Assert.Equal(modelId, result.Model);
    }
}
