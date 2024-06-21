// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.ClientModel.Primitives;
using System.Net.Http;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Extensions;

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
        var pipelineMessage = ClientPipeline.Create().CreateMessage();

        response.Response

        pipelineMessage.Content = "content";
        pipelineMessage.StatusCode = 200;
        var exception = new ClientResultException("message", pipelineMessage);

        // Act
        var httpOperationException = exception.ToHttpOperationException();

        // Assert
        Assert.NotNull(httpOperationException);
        Assert.Equal(exception, httpOperationException.InnerException);
        Assert.Equal(exception.Message, httpOperationException.Message);
        Assert.Equal(pipelineMessage.Content, httpOperationException.ResponseContent);
        Assert.Equal(pipelineMessage.StatusCode, httpOperationException.StatusCode);
    }
}
