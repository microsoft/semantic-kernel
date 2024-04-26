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
                ResultParser = (result) => result.GetValue<string>() ?? string.Empty,
            };

        Assert.Null(strategy.Arguments);
        Assert.NotNull(strategy.Kernel);
        Assert.NotNull(strategy.ResultParser);

        Agent nextAgent = await strategy.NextAsync([mockAgent.Object], []);

        Assert.NotNull(nextAgent);
        Assert.Equal(mockAgent.Object, nextAgent);
    }

    /// <summary>
    /// Verify strategy mismatch.
    /// </summary>
    [Fact]
    public async Task VerifyKernelFunctionSelectionStrategyParsingAsync()
    {
        Mock<Agent> mockAgent = new();
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new TestPlugin(string.Empty));

        KernelFunctionSelectionStrategy strategy =
            new(plugin.Single(), new())
            {
                Arguments = new(new OpenAIPromptExecutionSettings()) { { "key", mockAgent.Object.Name } },
                ResultParser = (result) => result.GetValue<string>() ?? string.Empty,
            };

        await Assert.ThrowsAsync<KernelException>(() => strategy.NextAsync([mockAgent.Object], []));
    }

    private sealed class TestPlugin(string agentName)
    {
        [KernelFunction]
        public string GetValue() => agentName;
    }
}
