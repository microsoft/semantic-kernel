// Copyright (c) Microsoft. All rights reserved.
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.Chat;

/// <summary>
/// Unit testing of <see cref="KernelFunctionSelectionStrategy"/>.
/// </summary>
public class KernelFunctionSelectionStrategyTests
{
    /// <summary>
    /// Verify default state and behavior
    /// </summary>
    [Fact]
    public async Task VerifyKernelFunctionSelectionStrategyDefaultsAsync()
    {
        // Arrange
        MockAgent mockAgent = new();
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new TestPlugin(mockAgent.Id));

        KernelFunctionSelectionStrategy strategy =
            new(plugin.Single(), new())
            {
                ResultParser = (result) => mockAgent.Id,
                AgentsVariableName = "agents",
                HistoryVariableName = "history",
            };

        // Assert
        Assert.Null(strategy.Arguments);
        Assert.NotNull(strategy.Kernel);
        Assert.NotNull(strategy.ResultParser);
        Assert.NotEqual("agent", KernelFunctionSelectionStrategy.DefaultAgentsVariableName);
        Assert.NotEqual("history", KernelFunctionSelectionStrategy.DefaultHistoryVariableName);

        // Act
        Agent nextAgent = await strategy.NextAsync([mockAgent], []);

        // Assert
        Assert.NotNull(nextAgent);
        Assert.Equal(mockAgent, nextAgent);
    }

    /// <summary>
    /// Verify strategy mismatch.
    /// </summary>
    [Fact]
    public async Task VerifyKernelFunctionSelectionStrategyThrowsOnNullResultAsync()
    {
        // Arrange
        MockAgent mockAgent = new();
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new TestPlugin(mockAgent.Id));

        KernelFunctionSelectionStrategy strategy =
            new(plugin.Single(), new())
            {
                Arguments = new(new OpenAIPromptExecutionSettings()) { { "key", mockAgent.Name } },
                ResultParser = (result) => "larry",
            };

        // Act and Assert
        await Assert.ThrowsAsync<KernelException>(() => strategy.NextAsync([mockAgent], []));
    }

    /// <summary>
    /// Verify strategy mismatch.
    /// </summary>
    [Fact]
    public async Task VerifyKernelFunctionSelectionStrategyThrowsOnBadResultAsync()
    {
        // Arrange
        MockAgent mockAgent = new();
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new TestPlugin(""));

        KernelFunctionSelectionStrategy strategy =
            new(plugin.Single(), new())
            {
                Arguments = new(new OpenAIPromptExecutionSettings()) { { "key", mockAgent.Name } },
                ResultParser = (result) => result.GetValue<string>() ?? null!,
            };

        // Act and Assert
        await Assert.ThrowsAsync<KernelException>(() => strategy.NextAsync([mockAgent], []));
    }

    private sealed class TestPlugin(string agentName)
    {
        [KernelFunction]
        public string GetValue() => agentName;
    }
}
