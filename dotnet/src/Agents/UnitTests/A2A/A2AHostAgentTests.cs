// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.A2A;
using Microsoft.SemanticKernel.ChatCompletion;
using SharpA2A.Core;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.A2A;

/// <summary>
/// Tests for the <see cref="A2AHostAgent"/> class.
/// </summary>
public sealed class A2AHostAgentTests : BaseA2AClientTest
{
    /// <summary>
    /// Tests that the constructor verifies parameters and throws <see cref="ArgumentNullException"/> when necessary.
    /// </summary>
    [Fact]
    public void ConstructorShouldVerifyParams()
    {
        // Arrange & Act & Assert
        Assert.Throws<ArgumentNullException>(() => new A2AHostAgent(null!, this.CreateAgentCard()));
        Assert.Throws<ArgumentNullException>(() => new A2AHostAgent(new MockAgent(), null!));
    }

    [Fact]
    public async Task VerifyExecuteAgentTaskAsync()
    {
        // Arrange
        var agent = new MockAgent();
        var taskManager = new TaskManager();
        var hostAgent = new A2AHostAgent(agent, this.CreateAgentCard(), taskManager);

        // Act
        var agentTask = await taskManager.CreateTaskAsync();
        agentTask.History = this.CreateUserMessages(["Hello"]);
        await hostAgent.ExecuteAgentTaskAsync(agentTask);

        // Assert
        Assert.NotNull(agentTask);
        Assert.NotNull(agentTask.Artifacts);
        Assert.Single(agentTask.Artifacts);
        Assert.NotNull(agentTask.Artifacts[0].Parts);
        Assert.Single(agentTask.Artifacts[0].Parts);
        Assert.Equal("Mock Response", agentTask.Artifacts[0].Parts[0].AsTextPart().Text);
    }

    #region private
    private List<Message> CreateUserMessages(string[] userMessages)
    {
        var messages = new List<Message>();

        foreach (var userMessage in userMessages)
        {
            messages.Add(new Message()
            {
                Role = MessageRole.User,
                Parts = [new TextPart() { Text = userMessage }],
            });
        }

        return messages;
    }
    #endregion
}

internal sealed class MockAgent : Agent
{
    public override async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(ICollection<ChatMessageContent> messages, AgentThread? thread = null, AgentInvokeOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await Task.Delay(100, cancellationToken);

        yield return new AgentResponseItem<ChatMessageContent>(new ChatMessageContent(AuthorRole.Assistant, "Mock Response"), thread ?? new MockAgentThread());
    }

    public override async IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(ICollection<ChatMessageContent> messages, AgentThread? thread = null, AgentInvokeOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await Task.Delay(100, cancellationToken);

        yield return new AgentResponseItem<StreamingChatMessageContent>(new StreamingChatMessageContent(AuthorRole.Assistant, "Mock Streaming Response"), thread ?? new MockAgentThread());
    }

    protected internal override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        throw new NotImplementedException();
    }

    protected internal override IEnumerable<string> GetChannelKeys()
    {
        throw new NotImplementedException();
    }

    protected internal override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
    {
        throw new NotImplementedException();
    }
}

internal sealed class MockAgentThread : AgentThread
{
    protected override Task<string?> CreateInternalAsync(CancellationToken cancellationToken)
    {
        throw new NotImplementedException();
    }

    protected override Task DeleteInternalAsync(CancellationToken cancellationToken)
    {
        throw new NotImplementedException();
    }

    protected override Task OnNewMessageInternalAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }
}
