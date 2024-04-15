// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.Google.Core;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Core.VertexAI;

public sealed class VertexAIEmbeddingRequestTests
{
    [Fact]
    public void FromDataReturnsValidRequestWithData()
    {
        // Arrange
        string[] data = ["text1", "text2"];

        // Act
        var request = VertexAIEmbeddingRequest.FromData(data);

        // Assert
        Assert.Equal(2, request.Requests.Count);
        Assert.Equal(data[0], request.Requests[0].Content);
        Assert.Equal(data[1], request.Requests[1].Content);
    }
}
