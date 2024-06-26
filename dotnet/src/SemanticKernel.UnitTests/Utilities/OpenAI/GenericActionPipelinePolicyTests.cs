// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel.Primitives;
using Xunit;

namespace SemanticKernel.UnitTests.Utilities.OpenAI;

public class GenericActionPipelinePolicyTests
{
    [Fact]
    public void ItCanBeInstantiated()
    {
        // Act
        var addHeaderRequestPolicy = new GenericActionPipelinePolicy((message) => { });

        // Assert
        Assert.NotNull(addHeaderRequestPolicy);
    }

    [Fact]
    public void ItProcessAddsHeaderToRequest()
    {
        // Arrange
        var headerName = "headerName";
        var headerValue = "headerValue";
        var sut = new GenericActionPipelinePolicy((message) => { message.Request.Headers.Add(headerName, headerValue); });

        var pipeline = ClientPipeline.Create();
        var message = pipeline.CreateMessage();

        // Act
        sut.Process(message, [sut], 0);

        // Assert
        message.Request.Headers.TryGetValue(headerName, out var value);
        Assert.NotNull(value);
        Assert.Equal(headerValue, value);
    }
}
