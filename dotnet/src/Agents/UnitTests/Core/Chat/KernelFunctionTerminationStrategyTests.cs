// Copyright (c) Microsoft. All rights reserved.
using System;
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
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new TestPlugin());

        KernelFunctionTerminationStrategy strategy = new(plugin.Single());

        Assert.Null(strategy.Arguments);
        Assert.NotNull(strategy.Kernel);
        Assert.NotNull(strategy.ResultParser);

        Mock<Agent> mockAgent = new();

        bool isTerminating = await strategy.ShouldTerminateAsync(mockAgent.Object, []);

        Assert.False(isTerminating);
    }

    /// <summary>
    /// Verify strategy with result parser.
    /// </summary>
    [Fact]
    public async Task VerifyKernelFunctionTerminationStrategyParsingAsync()
    {
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new TestPlugin());

        KernelFunctionTerminationStrategy strategy =
            new(plugin.Single())
            {
                Arguments = new(new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions }) { { "key", "test" } },
                Kernel = Kernel.CreateBuilder().Build(),
                ResultParser = new TestParser()
            };

        Mock<Agent> mockAgent = new();

        bool isTerminating = await strategy.ShouldTerminateAsync(mockAgent.Object, []);

        Assert.True(isTerminating);
    }

    private sealed class TestParser : FunctionResultProcessor<bool>
    {
        protected override bool ProcessTextResult(string result)
        {
            return result.Equals("test", StringComparison.OrdinalIgnoreCase);
        }
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
