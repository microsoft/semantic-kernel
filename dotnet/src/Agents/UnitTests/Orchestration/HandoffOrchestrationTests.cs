// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Handoff;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Orchestration;

/// <summary>
/// Tests for the <see cref="HandoffOrchestration"/> class.
/// </summary>
public class HandoffOrchestrationTests
{
    [Fact]
    public async Task HandoffOrchestrationWithSingleAgentAsync()
    {
        // Arrange
        await using InProcessRuntime runtime = new();
        MockAgent mockAgent1 = CreateMockAgent(2, "xyz");

        // Act: Create and execute the orchestration
        string response = await ExecuteOrchestrationAsync(runtime, handoffs: null, mockAgent1);

        // Assert
        Assert.Equal("xyz", response);
        Assert.Equal(1, mockAgent1.InvokeCount);
    }

    [Fact]
    public async Task HandoffOrchestrationWithMultipleAgentsAsync()
    {
        // Arrange
        await using InProcessRuntime runtime = new();

        MockAgent mockAgent1 = CreateMockAgent(1, "abc");
        MockAgent mockAgent2 = CreateMockAgent(2, "xyz");
        MockAgent mockAgent3 = CreateMockAgent(3, "lmn");

        // Act: Create and execute the orchestration
        string response = await ExecuteOrchestrationAsync(
            runtime,
            handoffs:
                new()
                {
                    {
                        mockAgent1.Name!,
                        new()
                        {
                            { mockAgent2.Name!, mockAgent2.Description! },
                        }
                    },
                    {
                        mockAgent2  .Name!,
                        new()
                        {
                            { mockAgent3.Name!, mockAgent3.Description! },
                        }
                    },
                    {
                        mockAgent3.Name!,
                        new()
                        {
                            { mockAgent1.Name!, mockAgent1.Description! },
                        }
                    },
                },
            mockAgent1,
            mockAgent2,
            mockAgent3);

        // Assert
        Assert.Equal("lmn", response);
        Assert.Equal(1, mockAgent1.InvokeCount);
        Assert.Equal(1, mockAgent2.InvokeCount);
        Assert.Equal(1, mockAgent3.InvokeCount);
    }

    private static async Task<string> ExecuteOrchestrationAsync(InProcessRuntime runtime, Dictionary<string, HandoffConnections>? handoffs, params OrchestrationTarget[] mockAgents)
    {
        // Act
        await runtime.StartAsync();

        HandoffOrchestration orchestration = new(runtime, handoffs ?? [], mockAgents);

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
            Name = $"agent{index}",
            Description = $"Provides a mock response",
            Response = [new(AuthorRole.Assistant, response)]
        };
    }
}
