// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.Chat;

/// <summary>
/// Unit testing of <see cref="KernelFunctionTerminationStrategy"/>.
/// </summary>
public class KernelFunctionTerminationStrategyTests
{
    /// <summary>
    /// Verify default state and behavior
    /// </summary>
    [Fact]
    public async Task VerifyKernelFunctionTerminationStrategyDefaultsAsync()
    {
        // Arrange
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new TestPlugin());

        KernelFunctionTerminationStrategy strategy =
            new(plugin.Single(), new())
            {
                AgentVariableName = "agent",
                HistoryVariableName = "history",
            };

        // Assert
        Assert.Null(strategy.Arguments);
        Assert.NotNull(strategy.Kernel);
        Assert.NotNull(strategy.ResultParser);
        Assert.NotEqual("agent", KernelFunctionTerminationStrategy.DefaultAgentVariableName);
        Assert.NotEqual("history", KernelFunctionTerminationStrategy.DefaultHistoryVariableName);

        // Act
        MockAgent mockAgent = new();
        bool isTerminating = await strategy.ShouldTerminateAsync(mockAgent, []);

        Assert.True(isTerminating);
    }

    /// <summary>
    /// Verify strategy with result parser.
    /// </summary>
    [Fact]
    public async Task VerifyKernelFunctionTerminationStrategyParsingAsync()
    {
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new TestPlugin());

        KernelFunctionTerminationStrategy strategy =
            new(plugin.Single(), new())
            {
                Arguments = new(new OpenAIPromptExecutionSettings()) { { "key", "test" } },
                ResultParser = (result) => string.Equals("test", result.GetValue<string>(), StringComparison.OrdinalIgnoreCase)
            };

        MockAgent mockAgent = new();

        bool isTerminating = await strategy.ShouldTerminateAsync(mockAgent, []);

        Assert.True(isTerminating);
    }

    private sealed class TestPlugin()
    {
        [KernelFunction]
        public string GetValue(KernelArguments? arguments)
        {
            string? argument = arguments?.First().Value?.ToString();
            return argument ?? string.Empty;
        }
    }
}
