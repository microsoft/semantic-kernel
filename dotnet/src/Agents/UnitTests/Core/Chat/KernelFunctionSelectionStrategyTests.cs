// Copyright (c) Microsoft. All rights reserved.
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Moq;
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
        Mock<Agent> mockAgent = new();
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new TestPlugin(mockAgent.Object.Id));

        KernelFunctionSelectionStrategy strategy =
            new(plugin.Single(), new())
            {
                AgentsVariableName = "_a_",
                HistoryVariableName = "_h_",
                ResultParser = (result) => result.GetValue<string>() ?? string.Empty,
            };

        Assert.Null(strategy.Arguments);
        Assert.NotNull(strategy.Kernel);
        Assert.NotNull(strategy.ResultParser);
        Assert.Equal("_a_", strategy.AgentsVariableName);
        Assert.Equal("_h_", strategy.HistoryVariableName);

        Agent nextAgent = await strategy.NextAsync([mockAgent.Object], []);

        Assert.NotNull(nextAgent);
        Assert.Equal(mockAgent.Object, nextAgent);
    }
    /// <summary>
    /// Verify default state and behavior
    /// </summary>
    [Fact]
    public async Task VerifyKernelFunctionSelectionStrategyInitialAgentAsync()
    {
        Mock<Agent> mockAgent1 = new();
        Mock<Agent> mockAgent2 = new();
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new TestPlugin(mockAgent2.Object.Id));

        KernelFunctionSelectionStrategy strategy =
            new(plugin.Single(), new())
            {
                InitialAgent = mockAgent1.Object,
                ResultParser = (result) => result.GetValue<string>() ?? string.Empty,
            };

        Agent nextAgent = await strategy.NextAsync([mockAgent2.Object], []);

        Assert.NotNull(nextAgent);
        Assert.Equal(mockAgent1.Object, nextAgent);
    }

    /// <summary>
    /// Verify strategy mismatch.
    /// </summary>
    [Fact]
    public async Task VerifyKernelFunctionSelectionStrategyNullAgentAsync()
    {
        Mock<Agent> mockAgent = new();
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new TestPlugin(null));

        KernelFunctionSelectionStrategy strategy =
            new(plugin.Single(), new())
            {
                Arguments = new(new OpenAIPromptExecutionSettings()) { { "key", mockAgent.Object.Name } },
            };

        await Assert.ThrowsAsync<KernelException>(() => strategy.NextAsync([mockAgent.Object], []));

        strategy =
            new(plugin.Single(), new())
            {
                Arguments = new(new OpenAIPromptExecutionSettings()) { { "key", mockAgent.Object.Name } },
                UseInitialAgentAsFallback = true
            };

        await Assert.ThrowsAsync<KernelException>(() => strategy.NextAsync([mockAgent.Object], []));
    }

    /// <summary>
    /// Verify strategy mismatch.
    /// </summary>
    [Fact]
    public async Task VerifyKernelFunctionSelectionStrategyBadAgentFallbackWithNoInitialAgentAsync()
    {
        Mock<Agent> mockAgent = new();
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new TestPlugin("bad"));

        KernelFunctionSelectionStrategy strategy =
            new(plugin.Single(), new())
            {
                Arguments = new(new OpenAIPromptExecutionSettings()) { { "key", mockAgent.Object.Name } },
            };

        await Assert.ThrowsAsync<KernelException>(() => strategy.NextAsync([mockAgent.Object], []));

        strategy =
            new(plugin.Single(), new())
            {
                Arguments = new(new OpenAIPromptExecutionSettings()) { { "key", mockAgent.Object.Name } },
                UseInitialAgentAsFallback = true
            };

        await Assert.ThrowsAsync<KernelException>(() => strategy.NextAsync([mockAgent.Object], []));
    }

    /// <summary>
    /// Verify strategy mismatch.
    /// </summary>
    [Fact]
    public async Task VerifyKernelFunctionSelectionStrategyBadAgentFallbackAsync()
    {
        Mock<Agent> mockAgent = new();
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new TestPlugin("bad"));

        KernelFunctionSelectionStrategy strategy =
            new(plugin.Single(), new())
            {
                Arguments = new(new OpenAIPromptExecutionSettings()) { { "key", mockAgent.Object.Name } },
                InitialAgent = mockAgent.Object,
                UseInitialAgentAsFallback = true
            };

        Agent nextAgent = await strategy.NextAsync([mockAgent.Object], []);

        Assert.NotNull(nextAgent);
        Assert.Equal(mockAgent.Object, nextAgent);
    }

    private sealed class TestPlugin(string? agentName)
    {
        [KernelFunction]
        public string? GetValue() => agentName;
    }
}
