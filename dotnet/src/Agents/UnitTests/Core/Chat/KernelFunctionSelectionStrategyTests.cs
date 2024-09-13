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
                AgentsVariableName = "_a_",
                HistoryVariableName = "_h_",
                ResultParser = (result) => result.GetValue<string>() ?? string.Empty,
            };

        // Assert
        Assert.Null(strategy.Arguments);
        Assert.NotNull(strategy.Kernel);
        Assert.NotNull(strategy.ResultParser);
        Assert.Equal("_a_", strategy.AgentsVariableName);
        Assert.Equal("_h_", strategy.HistoryVariableName);

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
    /// Verify default state and behavior
    /// </summary>
    [Fact]
    public async Task VerifyKernelFunctionSelectionStrategyInitialAgentAsync()
    {
        MockAgent mockAgent1 = new();
        MockAgent mockAgent2 = new();
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new TestPlugin(mockAgent2.Id));

        KernelFunctionSelectionStrategy strategy =
            new(plugin.Single(), new())
            {
                InitialAgent = mockAgent1,
                ResultParser = (result) => result.GetValue<string>() ?? string.Empty,
            };

        Agent nextAgent = await strategy.NextAsync([mockAgent2], []);

        Assert.NotNull(nextAgent);
        Assert.Equal(mockAgent1, nextAgent);
    }

    /// <summary>
    /// Verify strategy mismatch.
    /// </summary>
    [Fact]
    public async Task VerifyKernelFunctionSelectionStrategyNullAgentAsync()
    {
        MockAgent mockAgent = new();
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new TestPlugin(null));

        KernelFunctionSelectionStrategy strategy =
            new(plugin.Single(), new())
            {
                Arguments = new(new OpenAIPromptExecutionSettings()) { { "key", mockAgent.Name } },
            };

        await Assert.ThrowsAsync<KernelException>(() => strategy.NextAsync([mockAgent], []));

        strategy =
            new(plugin.Single(), new())
            {
                Arguments = new(new OpenAIPromptExecutionSettings()) { { "key", mockAgent.Name } },
                UseInitialAgentAsFallback = true
            };

        await Assert.ThrowsAsync<KernelException>(() => strategy.NextAsync([mockAgent], []));
    }

    /// <summary>
    /// Verify strategy mismatch.
    /// </summary>
    [Fact]
    public async Task VerifyKernelFunctionSelectionStrategyBadAgentFallbackWithNoInitialAgentAsync()
    {
        // Arrange
        MockAgent mockAgent = new();
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new TestPlugin("bad"));

        KernelFunctionSelectionStrategy strategy =
            new(plugin.Single(), new())
            {
                Arguments = new(new OpenAIPromptExecutionSettings()) { { "key", mockAgent.Name } },
            };

        await Assert.ThrowsAsync<KernelException>(() => strategy.NextAsync([mockAgent], []));

        strategy =
            new(plugin.Single(), new())
            {
                Arguments = new(new OpenAIPromptExecutionSettings()) { { "key", mockAgent.Name } },
                UseInitialAgentAsFallback = true
            };

        // Act and Assert
        await Assert.ThrowsAsync<KernelException>(() => strategy.NextAsync([mockAgent], []));
    }

    /// <summary>
    /// Verify strategy mismatch.
    /// </summary>
    [Fact]
    public async Task VerifyKernelFunctionSelectionStrategyBadAgentFallbackAsync()
    {
        MockAgent mockAgent = new();
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new TestPlugin("bad"));

        KernelFunctionSelectionStrategy strategy =
            new(plugin.Single(), new())
            {
                Arguments = new(new OpenAIPromptExecutionSettings()) { { "key", mockAgent.Name } },
                InitialAgent = mockAgent,
                UseInitialAgentAsFallback = true
            };

        Agent nextAgent = await strategy.NextAsync([mockAgent], []);

        Assert.NotNull(nextAgent);
        Assert.Equal(mockAgent, nextAgent);
    }

    private sealed class TestPlugin(string? agentName)
    {
        [KernelFunction]
        public string? GetValue() => agentName;
    }
}
