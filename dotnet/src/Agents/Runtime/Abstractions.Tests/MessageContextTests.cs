// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using Xunit;

namespace Microsoft.SemanticKernel.Agents.Runtime.Abstractions.Tests;

[Trait("Category", "Unit")]
public class MessageContextTests
{
    [Fact]
    public void ConstructWithMessageIdAndCancellationTokenTest()
    {
        // Arrange
        string messageId = Guid.NewGuid().ToString();
        CancellationToken cancellationToken = new();

        // Act
        MessageContext messageContext = new(messageId, cancellationToken);

        // Assert
        Assert.Equal(messageId, messageContext.MessageId);
        Assert.Equal(cancellationToken, messageContext.CancellationToken);
    }

    [Fact]
    public void ConstructWithCancellationTokenTest()
    {
        // Arrange
        CancellationToken cancellationToken = new();

        // Act
        MessageContext messageContext = new(cancellationToken);

        // Assert
        Assert.NotNull(messageContext.MessageId);
        Assert.Equal(cancellationToken, messageContext.CancellationToken);
    }

    [Fact]
    public void AssignSenderTest()
    {
        // Arrange
        MessageContext messageContext = new(new CancellationToken());
        AgentId sender = new("type", "key");

        // Act
        messageContext.Sender = sender;

        // Assert
        Assert.Equal(sender, messageContext.Sender);
    }

    [Fact]
    public void AssignTopicTest()
    {
        // Arrange
        MessageContext messageContext = new(new CancellationToken());
        TopicId topic = new("type", "source");

        // Act
        messageContext.Topic = topic;

        // Assert
        Assert.Equal(topic, messageContext.Topic);
    }

    [Fact]
    public void AssignIsRpcPropertyTest()
    {
        // Arrange
        MessageContext messageContext = new(new CancellationToken())
        {
            // Act
            IsRpc = true
        };

        // Assert
        Assert.True(messageContext.IsRpc);
    }
}
