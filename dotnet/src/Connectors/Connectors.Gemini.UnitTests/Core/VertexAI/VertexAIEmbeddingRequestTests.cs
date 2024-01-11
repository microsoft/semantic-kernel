#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using Microsoft.SemanticKernel.Connectors.Gemini.Core.VertexAI;
using Xunit;

namespace SemanticKernel.Connectors.Gemini.UnitTests.Core.GoogleAI;

public sealed class VertexAIEmbeddingRequestTests
{
    [Fact]
    public void FromDataReturnsValidRequestWithData()
    {
        // Arrange
        var data = new[] { "text1", "text2" };
        var modelId = "modelId";

        // Act
        var request = VertexAIEmbeddingRequest.FromData(data, modelId);

        // Assert
        Assert.Equal(2, request.Requests.Count);
        Assert.Equal(data[0], request.Requests[0].Content);
        Assert.Equal(data[1], request.Requests[1].Content);
    }
}
