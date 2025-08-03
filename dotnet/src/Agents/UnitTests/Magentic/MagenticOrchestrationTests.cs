// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Magentic;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Magentic;

/// <summary>
/// Tests for the <see cref="MagenticOrchestration"/> class.
/// </summary>
public class MagenticOrchestrationTests
{
    [Fact]
    public async Task MagenticOrchestrationWithSingleAgentAsync()
    {
        // Arrange
        await using InProcessRuntime runtime = new();
        MockAgent mockAgent1 = CreateMockAgent(2, "xyz");

        // Act: Create and execute the orchestration
        string response = await this.ExecuteOrchestrationAsync(runtime, "answer", mockAgent1);

        // Assert
        Assert.Equal("answer", response);
        Assert.Equal(1, mockAgent1.InvokeCount);
    }

    [Fact]
    public async Task MagenticOrchestrationWithMultipleAgentsAsync()
    {
        // Arrange
        await using InProcessRuntime runtime = new();

        MockAgent mockAgent1 = CreateMockAgent(1, "abc");
        MockAgent mockAgent2 = CreateMockAgent(2, "xyz");
        MockAgent mockAgent3 = CreateMockAgent(3, "lmn");

        // Act: Create and execute the orchestration
        string response = await this.ExecuteOrchestrationAsync(runtime, "answer", mockAgent1, mockAgent2, mockAgent3);

        // Assert
        Assert.Equal("answer", response);
        Assert.Equal(1, mockAgent1.InvokeCount);
        Assert.Equal(0, mockAgent2.InvokeCount);
        Assert.Equal(0, mockAgent3.InvokeCount);
    }

    [Fact]
    public async Task MagenticOrchestrationMaxInvocationCountReached_WithoutPartialResultAsync()
    {
        // Arrange
        await using InProcessRuntime runtime = new();

        MockAgent mockAgent1 = CreateMockAgent(1, "abc");
        MockAgent mockAgent2 = CreateMockAgent(2, "xyz");
        MockAgent mockAgent3 = CreateMockAgent(3, "lmn");

        string jsonStatus =
            $$"""
            {
                "Name": "{{mockAgent1.Name}}",
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
        StandardMagenticManager manager = new(chatServiceMock.Object, settings)
        {
            MaximumInvocationCount = 1, // Fast failure for testing
        };

        MagenticOrchestration orchestration = new(manager, [mockAgent1, mockAgent2, mockAgent3]);

        // Act
        await runtime.StartAsync();

        const string InitialInput = "123";
        OrchestrationResult<string> result = await orchestration.InvokeAsync(InitialInput, runtime);
        string response = await result.GetValueAsync(TimeSpan.FromSeconds(20));

        // Assert
        Assert.NotNull(response);
        Assert.Contains("No partial result available.", response);
    }

    [Fact]
    public async Task MagenticOrchestrationMaxInvocationCountReached_WithPartialResultAsync()
    {
        // Arrange
        await using InProcessRuntime runtime = new();

        MockAgent mockAgent1 = CreateMockAgent(1, "abc");
        MockAgent mockAgent2 = CreateMockAgent(2, "xyz");
        MockAgent mockAgent3 = CreateMockAgent(3, "lmn");

        string jsonStatus =
            $$"""
            {
                "Name": "{{mockAgent1.Name}}",
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
        StandardMagenticManager manager = new(chatServiceMock.Object, settings)
        {
            MaximumInvocationCount = 2, // Fast failure for testing but at least one invocation
        };

        MagenticOrchestration orchestration = new(manager, [mockAgent1, mockAgent2, mockAgent3]);

        // Act
        await runtime.StartAsync();

        const string InitialInput = "123";
        OrchestrationResult<string> result = await orchestration.InvokeAsync(InitialInput, runtime);
        string response = await result.GetValueAsync(TimeSpan.FromSeconds(20));

        // Assert
        Assert.NotNull(response);
        Assert.Equal("abc", response);
    }

    [Fact]
    public async Task MagenticOrchestrationMaxResetCountReached_WithoutPartialResultAsync()
    {
        // Arrange
        await using InProcessRuntime runtime = new();

        MockAgent mockAgent1 = CreateMockAgent(1, "abc");
        MockAgent mockAgent2 = CreateMockAgent(2, "xyz");
        MockAgent mockAgent3 = CreateMockAgent(3, "lmn");

        string jsonStatus =
            $$"""
            {
                "Name": "{{mockAgent1.Name}}",
                "Instruction":"Proceed",
                "Reason":"TestReason",
                "IsTaskComplete": {
                  "Result": false,
                  "Reason": "Test"
                },
                "IsTaskProgressing": {
                  "Result": false,
                  "Reason": "Test"
                },
                "IsTaskInLoop": {
                  "Result": true,
                  "Reason": "Test"
                }
            }
            """;
        Mock<IChatCompletionService> chatServiceMock = CreateMockChatCompletionService(jsonStatus);

        FakePromptExecutionSettings settings = new();
        StandardMagenticManager manager = new(chatServiceMock.Object, settings)
        {
            MaximumResetCount = 1, // Fast failure for testing
            MaximumStallCount = 0, // No stalls allowed
        };

        MagenticOrchestration orchestration = new(manager, [mockAgent1, mockAgent2, mockAgent3]);

        // Act
        await runtime.StartAsync();

        const string InitialInput = "123";
        OrchestrationResult<string> result = await orchestration.InvokeAsync(InitialInput, runtime);
        string response = await result.GetValueAsync(TimeSpan.FromSeconds(20));

        // Assert
        Assert.NotNull(response);
        Assert.Contains("No partial result available.", response);
    }

    [Fact]
    public async Task MagenticOrchestrationMaxResetCountReached_WithPartialResultAsync()
    {
        // Arrange
        await using InProcessRuntime runtime = new();

        MockAgent mockAgent1 = CreateMockAgent(1, "abc");
        MockAgent mockAgent2 = CreateMockAgent(2, "xyz");
        MockAgent mockAgent3 = CreateMockAgent(3, "lmn");

        string jsonStatus =
            $$"""
            {
                "Name": "{{mockAgent1.Name}}",
                "Instruction":"Proceed",
                "Reason":"TestReason",
                "IsTaskComplete": {
                  "Result": false,
                  "Reason": "Test"
                },
                "IsTaskProgressing": {
                  "Result": false,
                  "Reason": "Test"
                },
                "IsTaskInLoop": {
                  "Result": true,
                  "Reason": "Test"
                }
            }
            """;
        Mock<IChatCompletionService> chatServiceMock = CreateMockChatCompletionService(jsonStatus);

        FakePromptExecutionSettings settings = new();
        StandardMagenticManager manager = new(chatServiceMock.Object, settings)
        {
            MaximumResetCount = 1, // Fast failure for testing but at least one response
            MaximumStallCount = 2,
        };

        MagenticOrchestration orchestration = new(manager, [mockAgent1, mockAgent2, mockAgent3]);

        // Act
        await runtime.StartAsync();

        const string InitialInput = "123";
        OrchestrationResult<string> result = await orchestration.InvokeAsync(InitialInput, runtime);
        string response = await result.GetValueAsync(TimeSpan.FromSeconds(20));

        // Assert
        Assert.NotNull(response);
        Assert.Contains("abc", response);
    }

    private async Task<string> ExecuteOrchestrationAsync(InProcessRuntime runtime, string answer, params Agent[] mockAgents)
    {
        // Act
        await runtime.StartAsync();

        Mock<MagenticManager> manager = this.CreateMockManager(answer);
        MagenticOrchestration orchestration = new(manager.Object, mockAgents);

        const string InitialInput = "123";
        OrchestrationResult<string> result = await orchestration.InvokeAsync(InitialInput, runtime);

        // Assert
        Assert.NotNull(result);

        // Act
        string response = await result.GetValueAsync(TimeSpan.FromSeconds(20));

        await runtime.RunUntilIdleAsync();

        return response;
    }

    private static MockAgent CreateMockAgent(int index, string response)
    {
        return new()
        {
            Name = $"MockAgent{index}",
            Description = $"test {index}",
            Response = [new(AuthorRole.Assistant, response)]
        };
    }

    private bool _isComplete = false;

    private Mock<MagenticManager> CreateMockManager(string answer)
    {
        Mock<MagenticManager> mockManager = new(MockBehavior.Strict);

        // Setup mock for PlanAsync method
        mockManager.Setup(m => m.PlanAsync(It.IsAny<MagenticManagerContext>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync((MagenticManagerContext context, CancellationToken _) => [new(AuthorRole.User, "test")]);

        // Setup mock for ReplanAsync method
        mockManager.Setup(m => m.ReplanAsync(It.IsAny<MagenticManagerContext>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync((MagenticManagerContext context, CancellationToken _) => [new(AuthorRole.User, "test")]);

        // Setup mock for EvaluateTaskProgressAsync method
        mockManager
            .Setup(m => m.EvaluateTaskProgressAsync(It.IsAny<MagenticManagerContext>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync((MagenticManagerContext context, CancellationToken _) => CreateLedger(false, context.Team.First().Key));

        // Setup mock for PrepareFinalAnswerAsync method
        mockManager.Setup(m => m.PrepareFinalAnswerAsync(It.IsAny<MagenticManagerContext>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync((MagenticManagerContext context, CancellationToken _) =>
                new ChatMessageContent(AuthorRole.Assistant, answer));

        return mockManager;

        MagenticProgressLedger CreateLedger(bool isTaskComplete, string name)
        {
            try
            {
                return
                    new(Name: name,
                        Instruction: "Test instruction",
                        Reason: "Test evaluation",
                        IsTaskComplete: new(this._isComplete, "test"),
                        IsTaskProgressing: new(true, "test"),
                        IsTaskInLoop: new(true, "test"));
            }
            finally
            {
                this._isComplete = true;
            }
        }
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

    private sealed class FakePromptExecutionSettings : PromptExecutionSettings
    {
        public override PromptExecutionSettings Clone()
        {
            return this;
        }

        public object? ResponseFormat { get; set; }
    }
}
