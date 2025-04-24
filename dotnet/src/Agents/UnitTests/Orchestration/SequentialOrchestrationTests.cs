// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Sequential;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Orchestration;

/// <summary>
/// Tests for the <see cref="SequentialOrchestration"/> class.
/// </summary>
public class SequentialOrchestrationTests
{
    [Fact]
    public async Task SequentialOrchestrationWithSingleAgentAsync()
    {
        // Arrange
        await using InProcessRuntime runtime = new();
        MockAgent mockAgent1 = CreateMockAgent(2, "xyz");

        // Act: Create and execute the orchestration
        string response = await ExecuteOrchestrationAsync(runtime, mockAgent1);

        // Assert
        Assert.Equal("xyz", response);
        Assert.Equal(1, mockAgent1.InvokeCount);
    }

    [Fact]
    public async Task SequentialOrchestrationWithMultipleAgentsAsync()
    {
        // Arrange
        await using InProcessRuntime runtime = new();

        MockAgent mockAgent1 = CreateMockAgent(1, "abc");
        MockAgent mockAgent2 = CreateMockAgent(2, "xyz");
        MockAgent mockAgent3 = CreateMockAgent(3, "lmn");

        // Act: Create and execute the orchestration
        string response = await ExecuteOrchestrationAsync(runtime, mockAgent1, mockAgent2, mockAgent3);

        // Assert
        Assert.Equal("lmn", response);
        Assert.Equal(1, mockAgent1.InvokeCount);
        Assert.Equal(1, mockAgent2.InvokeCount);
        Assert.Equal(1, mockAgent3.InvokeCount);
    }

    [Fact]
    public async Task SequentialOrchestrationWithNestedMemberAsync()
    {
        // Arrange
        await using InProcessRuntime runtime = new();

        MockAgent mockAgentB = CreateMockAgent(2, "efg");
        SequentialOrchestration<SequentialMessage, SequentialMessage> orchestration = CreateNested(runtime, mockAgentB);
        MockAgent mockAgent1 = CreateMockAgent(2, "xyz");

        // Act: Create and execute the orchestration
        string response = await ExecuteOrchestrationAsync(runtime, mockAgent1, orchestration);

        // Assert
        Assert.Equal("efg", response);
        Assert.Equal(1, mockAgent1.InvokeCount);
        Assert.Equal(1, mockAgentB.InvokeCount);
    }

    private static async Task<string> ExecuteOrchestrationAsync(InProcessRuntime runtime, params OrchestrationTarget[] mockAgents)
    {
        // Act
        await runtime.StartAsync();

        SequentialOrchestration orchestration = new(runtime, mockAgents);

        const string InitialInput = "123";
        OrchestrationResult<string> result = await orchestration.InvokeAsync(InitialInput);

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
            Description = $"test {index}",
            Response = [new(AuthorRole.Assistant, response)]
        };
    }

    private static SequentialOrchestration<SequentialMessage, SequentialMessage> CreateNested(InProcessRuntime runtime, params OrchestrationTarget[] targets)
    {
        return new(runtime, targets)
        {
            InputTransform = (SequentialMessage input) => ValueTask.FromResult(input),
            ResultTransform = (SequentialMessage results) => ValueTask.FromResult(results),
        };
    }
}
