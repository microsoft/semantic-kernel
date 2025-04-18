// Copyright (c) Microsoft. All rights reserved.
// MessageDeliveryTests.cs

using Xunit;

namespace Microsoft.AgentRuntime.InProcess.Tests;

[Trait("Category", "Unit")]
public class MessageDeliveryTests
{
    [Fact]
    public void Constructor_InitializesProperties()
    {
        // Arrange
        MessageEnvelope message = new(new object());
        Func<MessageEnvelope, CancellationToken, ValueTask> servicer = (_, _) => new ValueTask();
        ResultSink<object?> resultSink = new();

        // Act
        MessageDelivery delivery = new(message, servicer, resultSink);

        // Assert
        Assert.Same(message, delivery.Message);
        Assert.Same(servicer, delivery.Servicer);
        Assert.Same(resultSink, delivery.ResultSink);
    }

    [Fact]
    public async Task Future_WithResultSink_ReturnsSinkFuture()
    {
        // Arrange
        MessageEnvelope message = new(new object());
        Func<MessageEnvelope, CancellationToken, ValueTask> servicer = (_, _) => new ValueTask();

        ResultSink<object?> resultSink = new();
        int expectedResult = 42;
        resultSink.SetResult(expectedResult);

        // Act
        MessageDelivery delivery = new(message, servicer, resultSink);
        object? result = await delivery.ResultSink.Future;

        // Assert
        Assert.Equal(expectedResult, result);
    }

    [Fact]
    public async Task InvokeAsync_CallsServicerWithCorrectParameters()
    {
        // Arrange
        MessageEnvelope message = new(new object());
        CancellationToken cancellationToken = new();

        bool servicerCalled = false;
        MessageEnvelope? passedMessage = null;
        CancellationToken? passedToken = null;

        Func<MessageEnvelope, CancellationToken, ValueTask> servicer = (msg, token) =>
        {
            servicerCalled = true;
            passedMessage = msg;
            passedToken = token;
            return ValueTask.CompletedTask;
        };

        ResultSink<object?> sink = new();
        MessageDelivery delivery = new(message, servicer, sink);

        // Act
        await delivery.InvokeAsync(cancellationToken);

        // Assert
        Assert.True(servicerCalled);
        Assert.Same(message, passedMessage);
        Assert.Equal(cancellationToken, passedToken);
    }
}
