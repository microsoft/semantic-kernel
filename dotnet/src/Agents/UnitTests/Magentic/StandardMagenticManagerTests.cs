// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Magentic;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Magentic;

public class StandardMagenticManagerTests
{
    [Fact]
    public async Task PlanAsync_ReturnsLedgerAsync()
    {
        // Arrange
        Mock<IChatCompletionService> chatServiceMock = CreateMockChatCompletionService("TaskLedgerResponse");
        FakePromptExecutionSettings settings = new();
        MagenticTeam team = CreateMagenticTeam();
        MagenticManagerContext context = CreateMagenticContext(team, "Test Task", "History");
        StandardMagenticManager manager = new(chatServiceMock.Object, settings);

        // Act
        IList<ChatMessageContent> result = await manager.PlanAsync(context, CancellationToken.None);

        // Assert - ledger message should come from the LedgerTemplate.
        Assert.Single(result);
        ChatMessageContent ledgerMessage = result[0];
        Assert.Equal(AuthorRole.System, ledgerMessage.Role);
        Assert.Contains("TaskLedgerResponse", ledgerMessage.Content);
    }

    [Fact]
    public async Task ReplanAsync_ReturnsLedgerAsync()
    {
        // Arrange
        Mock<IChatCompletionService> chatServiceMock = CreateMockChatCompletionService("TaskLedgerResponse");
        FakePromptExecutionSettings settings = new();
        MagenticTeam team = CreateMagenticTeam();
        MagenticManagerContext context = CreateMagenticContext(team, "Test Task", "History");
        StandardMagenticManager manager = new(chatServiceMock.Object, settings);

        // Act
        IList<ChatMessageContent> result = await manager.ReplanAsync(context, CancellationToken.None);

        // Assert 
        Assert.Single(result);
        ChatMessageContent ledgerMessage = result[0];
        Assert.Equal(AuthorRole.System, ledgerMessage.Role);
        Assert.Contains("TaskLedgerResponse", ledgerMessage.Content);
    }

    [Fact]
    public async Task EvaluateTaskProgressAsync_ReturnsLedgerObjectAsync()
    {
        // Arrange
        string jsonStatus =
            """
            {
                "Name":"TestAgent",
                "Instruction":"Proceed",
                "Reason":"TestReason",
                "IsTaskComplete": {
                  "Result": false,
                  "Reason": "Test"
                },
                "IsTaskProgressing": {
                  "Result": true,
                  "Reason": "Test"
                },
                "IsTaskInLoop": {
                  "Result": false,
                  "Reason": "Test"
                }
            }            
            """;
        Mock<IChatCompletionService> chatServiceMock = CreateMockChatCompletionService(jsonStatus);

        FakePromptExecutionSettings settings = new();

        MagenticTeam team = CreateMagenticTeam();
        MagenticManagerContext context = CreateMagenticContext(team, "Test Task", "History");

        StandardMagenticManager manager = new(chatServiceMock.Object, settings);

        // Act
        MagenticProgressLedger result = await manager.EvaluateTaskProgressAsync(context, CancellationToken.None);

        // Assert
        Assert.Equal("TestAgent", result.Name);
        Assert.Equal("Proceed", result.Instruction);
        Assert.Equal("TestReason", result.Reason);
        Assert.False(result.IsTaskComplete);
        Assert.True(result.IsTaskProgressing);
        Assert.False(result.IsTaskInLoop);
    }

    [Fact]
    public async Task PrepareFinalAnswerAsync_ReturnsFinalAnswerAsync()
    {
        // Arrange
        Mock<IChatCompletionService> chatServiceMock = CreateMockChatCompletionService("FinalAnswerResponse");
        MagenticTeam team = CreateMagenticTeam();
        MagenticManagerContext context = CreateMagenticContext(team, "Test Task", "History");
        FakePromptExecutionSettings settings = new();
        StandardMagenticManager manager = new(chatServiceMock.Object, settings);

        // Act
        ChatMessageContent result = await manager.PrepareFinalAnswerAsync(context, CancellationToken.None);

        // Assert
        Assert.Equal(AuthorRole.Assistant, result.Role);
        Assert.Equal("FinalAnswerResponse", result.Content);
    }

    private static Mock<IChatCompletionService> CreateMockChatCompletionService(string response)
    {
        Mock<IChatCompletionService> chatServiceMock = new(MockBehavior.Strict);

        chatServiceMock.Setup(
            (service) => service.GetChatMessageContentsAsync(
                It.IsAny<ChatHistory>(),
                It.IsAny<PromptExecutionSettings>(),
                null,
                It.IsAny<CancellationToken>()))
            .ReturnsAsync([new ChatMessageContent(AuthorRole.Assistant, response)]);

        return chatServiceMock;
    }

    private static MagenticManagerContext CreateMagenticContext(MagenticTeam team, string inputTask, string history) =>
        new(team,
            [new ChatMessageContent(AuthorRole.User, inputTask)],
            [new ChatMessageContent(AuthorRole.User, history)],
            responseCount: 5,
            stallCount: 1,
            resetCount: 0);

    private static MagenticTeam CreateMagenticTeam() =>
        new()
        {
            { "Agent1", ("AgentType1", "Description1") },
            { "Agent2", ("AgentType2", "Description2") },
        };

    private sealed class FakePromptExecutionSettings : PromptExecutionSettings
    {
        public override PromptExecutionSettings Clone()
        {
            return this;
        }

        public object? ResponseFormat { get; set; }
    }
}
