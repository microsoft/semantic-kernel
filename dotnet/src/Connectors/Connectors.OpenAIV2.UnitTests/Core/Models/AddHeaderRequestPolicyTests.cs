// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel.Primitives;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Core.Models;

public class AddHeaderRequestPolicyTests
{
    [Fact]
    public void ItCanBeInstantiated()
    {
        // Arrange
        var headerName = "headerName";
        var headerValue = "headerValue";

        // Act
        var addHeaderRequestPolicy = new AddHeaderRequestPolicy(headerName, headerValue);

        // Assert
        Assert.NotNull(addHeaderRequestPolicy);
    }

    [Fact]
    public void ItOnSendingRequestAddsHeaderToRequest()
    {
        // Arrange
        var headerName = "headerName";
        var headerValue = "headerValue";
        var addHeaderRequestPolicy = new AddHeaderRequestPolicy(headerName, headerValue);
        var pipeline = ClientPipeline.Create();
        var message = pipeline.CreateMessage();

        // Act
        addHeaderRequestPolicy.OnSendingRequest(message);

        // Assert
        message.Request.Headers.TryGetValue(headerName, out var value);
        Assert.NotNull(value);
        Assert.Equal(headerValue, value);
    }
}
