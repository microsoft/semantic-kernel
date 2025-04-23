﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Moq;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentWithStatePartConformance;

public abstract class AgentWithStatePartTests<TFixture>(Func<TFixture> createAgentFixture) : IAsyncLifetime
    where TFixture : AgentFixture
{
#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
    private TFixture _agentFixture;
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.

    protected TFixture Fixture => this._agentFixture;

    [Fact]
    public virtual async Task StatePartReceivesMessagesFromAgentAsync()
    {
        // Arrange
        var mockStatePart = new Mock<ConversationStatePart>() { CallBase = true };
        mockStatePart.Setup(x => x.OnNewMessageAsync(It.IsAny<string>(), It.IsAny<ChatMessage>(), It.IsAny<CancellationToken>()));

        var agent = this.Fixture.Agent;

        var agentThread = this.Fixture.GetNewThread();

        try
        {
            agentThread.StateParts.Add(mockStatePart.Object);

            // Act
            var inputMessage = "What is the capital of France?";
            var asyncResults1 = agent.InvokeAsync(inputMessage, agentThread);
            var result = await asyncResults1.FirstAsync();

            // Assert
            Assert.Contains("Paris", result.Message.Content);
            mockStatePart.Verify(x => x.OnNewMessageAsync(It.IsAny<string>(), It.Is<ChatMessage>(cm => cm.Text == inputMessage), It.IsAny<CancellationToken>()), Times.Once);
            mockStatePart.Verify(x => x.OnNewMessageAsync(It.IsAny<string>(), It.Is<ChatMessage>(cm => cm.Text == result.Message.Content), It.IsAny<CancellationToken>()), Times.Once);
        }
        finally
        {
            // Cleanup
            await this.Fixture.DeleteThread(agentThread);
        }
    }

    [Fact]
    public virtual async Task StatePartPreInvokeStateIsUsedByAgentAsync()
    {
        // Arrange
        var mockStatePart = new Mock<ConversationStatePart>() { CallBase = true };
        mockStatePart.Setup(x => x.OnModelInvokeAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>())).ReturnsAsync("User name is Caoimhe");

        var agent = this.Fixture.Agent;

        var agentThread = this.Fixture.GetNewThread();

        try
        {
            agentThread.StateParts.Add(mockStatePart.Object);

            // Act
            var inputMessage = "What is my name?.";
            var asyncResults1 = agent.InvokeAsync(inputMessage, agentThread);
            var result = await asyncResults1.FirstAsync();

            // Assert
            Assert.Contains("Caoimhe", result.Message.Content);
        }
        finally
        {
            // Cleanup
            await this.Fixture.DeleteThread(agentThread);
        }
    }

    public Task InitializeAsync()
    {
        this._agentFixture = createAgentFixture();
        return this._agentFixture.InitializeAsync();
    }

    public Task DisposeAsync()
    {
        return this._agentFixture.DisposeAsync();
    }
}
