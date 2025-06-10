// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockAgent;
using Amazon.BedrockAgentRuntime;
using Amazon.BedrockAgentRuntime.Model;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Bedrock;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Bedrock;

/// <summary>
/// Unit testing of <see cref="BedrockAgentChannel"/>.
/// </summary>
public class BedrockAgentChannelTests
{
    private readonly Amazon.BedrockAgent.Model.Agent _agentModel = new()
    {
        AgentId = "1234567890",
        AgentName = "testName",
        Description = "test description",
        Instruction = "Instruction must have at least 40 characters",
    };

    /// <summary>
    /// Verify the simple scenario of receiving messages in a <see cref="BedrockAgentChannel"/>.
    /// </summary>
    [Fact]
    public async Task VerifyReceiveAsync()
    {
        // Arrange
        BedrockAgentChannel channel = new();
        List<ChatMessageContent> history = this.CreateNormalHistory();

        // Act
        await channel.ReceiveAsync(history);

        // Assert
        Assert.Equal(2, await channel.GetHistoryAsync().CountAsync());
    }

    /// <summary>
    /// Verify the <see cref="BedrockAgentChannel"/> skips messages with empty content.
    /// </summary>
    [Fact]
    public async Task VerifyReceiveWithEmptyContentAsync()
    {
        // Arrange
        BedrockAgentChannel channel = new();
        List<ChatMessageContent> history = [
            new ChatMessageContent()
            {
                Role = AuthorRole.User,
            },
        ];

        // Act
        await channel.ReceiveAsync(history);

        // Assert
        Assert.Empty(await channel.GetHistoryAsync().ToArrayAsync());
    }

    /// <summary>
    /// Verify the channel inserts placeholders when the message sequence is incorrect.
    /// </summary>
    [Fact]
    public async Task VerifyReceiveWithIncorrectSequenceAsync()
    {
        // Arrange
        BedrockAgentChannel channel = new();
        List<ChatMessageContent> history = this.CreateIncorrectSequenceHistory();

        // Act
        await channel.ReceiveAsync(history);

        // Assert that a user message is inserted between the two agent messages.
        // Note that `GetHistoryAsync` returns the history in a reversed order.
        Assert.Equal(6, await channel.GetHistoryAsync().CountAsync());
        Assert.Equal(AuthorRole.User, (await channel.GetHistoryAsync().ToArrayAsync())[3].Role);
    }

    /// <summary>
    /// Verify the channel empties the history when reset.
    /// </summary>
    [Fact]
    public async Task VerifyResetAsync()
    {
        // Arrange
        BedrockAgentChannel channel = new();
        List<ChatMessageContent> history = this.CreateNormalHistory();

        // Act
        await channel.ReceiveAsync(history);

        // Assert
        Assert.NotEmpty(await channel.GetHistoryAsync().ToArrayAsync());

        // Act
        await channel.ResetAsync();

        // Assert
        Assert.Empty(await channel.GetHistoryAsync().ToArrayAsync());
    }

    /// <summary>
    /// Verify the channel correctly prepares the history for invocation.
    /// </summary>
    [Fact]
    public async Task VerifyInvokeAsync()
    {
        // Arrange
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();
        BedrockAgent agent = new(this._agentModel, mockClient.Object, mockRuntimeClient.Object);

        BedrockAgentChannel channel = new();
        List<ChatMessageContent> history = this.CreateIncorrectSequenceHistory();

        // Act
        async Task InvokeAgent()
        {
            await channel.ReceiveAsync(history);
            await foreach (var _ in channel.InvokeAsync(agent))
            {
                continue;
            }
        }

        // Assert
        await Assert.ThrowsAsync<HttpOperationException>(() => InvokeAgent());
        mockRuntimeClient.Verify(x => x.InvokeAgentAsync(
            It.Is<InvokeAgentRequest>(r =>
                r.AgentAliasId == BedrockAgent.WorkingDraftAgentAlias
                && r.AgentId == this._agentModel.AgentId
                && r.InputText == "[SILENCE]"   // Inserted by `EnsureLastMessageIsUser`.
                && r.SessionState.ConversationHistory.Messages.Count == 6   // There is also a user message inserted between the two agent messages.
            ),
            It.IsAny<CancellationToken>()
        ), Times.Once);
    }

    /// <summary>
    /// Verify the channel returns an empty stream when invoking with an empty history.
    /// </summary>
    [Fact]
    public async Task VerifyInvokeWithEmptyHistoryAsync()
    {
        // Arrange
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();
        BedrockAgent agent = new(this._agentModel, mockClient.Object, mockRuntimeClient.Object);

        BedrockAgentChannel channel = new();

        // Act
        List<ChatMessageContent> history = [];
        await foreach ((bool _, ChatMessageContent Message) in channel.InvokeAsync(agent))
        {
            history.Add(Message);
        }

        // Assert
        Assert.Empty(history);
    }

    /// <summary>
    /// Verify the channel correctly prepares the history for streaming invocation.
    /// </summary>
    [Fact]
    public async Task VerifyInvokeStreamAsync()
    {
        // Arrange
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();
        BedrockAgent agent = new(this._agentModel, mockClient.Object, mockRuntimeClient.Object);

        BedrockAgentChannel channel = new();
        List<ChatMessageContent> history = this.CreateIncorrectSequenceHistory();

        // Act
        async Task InvokeAgent()
        {
            await channel.ReceiveAsync(history);
            await foreach (var _ in channel.InvokeStreamingAsync(agent, []))
            {
                continue;
            }
        }

        // Assert
        await Assert.ThrowsAsync<HttpOperationException>(() => InvokeAgent());
        mockRuntimeClient.Verify(x => x.InvokeAgentAsync(
            It.Is<InvokeAgentRequest>(r =>
                r.AgentAliasId == BedrockAgent.WorkingDraftAgentAlias
                && r.AgentId == this._agentModel.AgentId
                && r.InputText == "[SILENCE]"   // Inserted by `EnsureLastMessageIsUser`.
                && r.SessionState.ConversationHistory.Messages.Count == 6   // There is also a user message inserted between the two agent messages.
            ),
            It.IsAny<CancellationToken>()
        ), Times.Once);
    }

    /// <summary>
    /// Verify the channel returns an empty stream when invoking with an empty history.
    /// </summary>
    [Fact]
    public async Task VerifyInvokeStreamingWithEmptyHistoryAsync()
    {
        // Arrange
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();
        BedrockAgent agent = new(this._agentModel, mockClient.Object, mockRuntimeClient.Object);

        BedrockAgentChannel channel = new();

        // Act
        List<StreamingChatMessageContent> history = [];
        await foreach (var message in channel.InvokeStreamingAsync(agent, []))
        {
            history.Add(message);
        }

        // Assert
        Assert.Empty(history);
    }

    private List<ChatMessageContent> CreateNormalHistory()
    {
        return
        [
            new ChatMessageContent(AuthorRole.User, "Hi!"),
            new ChatMessageContent(AuthorRole.Assistant, "Hi, how can I help you?"),
        ];
    }

    private List<ChatMessageContent> CreateIncorrectSequenceHistory()
    {
        return
        [
            new ChatMessageContent(AuthorRole.User, "What is a word that starts with 'x'?"),
            new ChatMessageContent(AuthorRole.Assistant, "Xylophone.")
            {
                AuthorName = "Agent 1"
            },
            new ChatMessageContent(AuthorRole.Assistant, "Xenon.")
            {
                AuthorName = "Agent 2"
            },
            new ChatMessageContent(AuthorRole.User, "Thanks!"),
            new ChatMessageContent(AuthorRole.Assistant, "Is there anything else you need?")
            {
                AuthorName = "Agent 1"
            },
        ];
    }

    private (Mock<IAmazonBedrockAgent>, Mock<IAmazonBedrockAgentRuntime>) CreateMockClients()
    {
        Mock<IAmazonBedrockAgent> mockClient = new();
        Mock<IAmazonBedrockAgentRuntime> mockRuntimeClient = new();
#pragma warning disable CA2000 // Dispose objects before losing scope
        mockRuntimeClient.Setup(x => x.InvokeAgentAsync(
            It.IsAny<InvokeAgentRequest>(),
            It.IsAny<CancellationToken>())
        ).ReturnsAsync(new InvokeAgentResponse()
        {
            // It's not important what the response is for this test.
            // And it's difficult to mock the response stream.
            // Tests should expect an exception to be thrown.
            HttpStatusCode = System.Net.HttpStatusCode.NotFound,
        });
#pragma warning restore CA2000 // Dispose objects before losing scope

        return (mockClient, mockRuntimeClient);
    }
}
