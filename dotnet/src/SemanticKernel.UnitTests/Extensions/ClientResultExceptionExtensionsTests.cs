// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using System.ClientModel.Primitives;
using Xunit;

namespace SemanticKernel.UnitTests.Utilities.OpenAI;

public class ClientResultExceptionExtensionsTests
{
    [Fact]
    public void ItCanRecoverFromResponseErrorAndConvertsToHttpOperationExceptionWithDefaultData()
    {
        // Arrange
        var exception = new ClientResultException("message", ClientPipeline.Create().CreateMessage().Response);

        // Act
        var httpOperationException = exception.ToHttpOperationException();

        // Assert
        Assert.NotNull(httpOperationException);
        Assert.Equal(exception, httpOperationException.InnerException);
        Assert.Equal(exception.Message, httpOperationException.Message);
        Assert.Null(httpOperationException.ResponseContent);
        Assert.Null(httpOperationException.StatusCode);
    }

    [Fact]
    public void ItCanProvideResponseContentAndStatusCode()
    {
        // Arrange
        using var pipelineResponse = new MockPipelineResponse();

        pipelineResponse.SetContent("content");
        pipelineResponse.SetStatus(200);

        var exception = new ClientResultException("message", pipelineResponse);

        // Act
        var httpOperationException = exception.ToHttpOperationException();

        // Assert
        Assert.NotNull(httpOperationException);
        Assert.NotNull(httpOperationException.StatusCode);
        Assert.Equal(exception, httpOperationException.InnerException);
        Assert.Equal(exception.Message, httpOperationException.Message);
        Assert.Equal(pipelineResponse.Content.ToString(), httpOperationException.ResponseContent);
        Assert.Equal(pipelineResponse.Status, (int)httpOperationException.StatusCode!);
    }

    [Fact]
    public void ItProvideStatusForResponsesWithoutContent()
    {
        // Arrange
        using var pipelineResponse = new MockPipelineResponse();

        pipelineResponse.SetStatus(200);

        var exception = new ClientResultException("message", pipelineResponse);

        // Act
        var httpOperationException = exception.ToHttpOperationException();

        // Assert
        Assert.NotNull(httpOperationException);
        Assert.NotNull(httpOperationException.StatusCode);
        Assert.Equal(exception, httpOperationException.InnerException);
        Assert.Equal(exception.Message, httpOperationException.Message);
        Assert.Equal(pipelineResponse.Status, (int)httpOperationException.StatusCode!);
    }
}
