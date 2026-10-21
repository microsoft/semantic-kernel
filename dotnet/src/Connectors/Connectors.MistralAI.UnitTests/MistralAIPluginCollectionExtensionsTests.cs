// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.MistralAI;
using Microsoft.SemanticKernel.Connectors.MistralAI.Client;
using Xunit;

namespace SemanticKernel.Connectors.MistralAI.UnitTests;

/// <summary>
/// Unit tests for <see cref="MistralAIPluginCollectionExtensions"/>.
/// </summary>
public sealed class MistralAIPluginCollectionExtensionsTests
{
    [Theory]
    [InlineData("")]
    [InlineData("  ")]
    public void ItTreatsEmptyFunctionArgumentsAsNoArguments(string arguments)
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromFunctions("MyPlugin", [KernelFunctionFactory.CreateFromMethod(() => "noon", "GetTime")]);
        var toolCallFunction = new MistralFunction("MyPlugin-GetTime", string.Empty, null) { Arguments = arguments };

        // Act
        bool found = kernel.Plugins.TryGetFunctionAndArguments(toolCallFunction, out KernelFunction? function, out KernelArguments? kernelArguments);

        // Assert
        Assert.True(found);
        Assert.NotNull(function);
        Assert.Null(kernelArguments);
    }
}
