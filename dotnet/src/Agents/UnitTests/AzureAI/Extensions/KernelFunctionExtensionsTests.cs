// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ComponentModel;
using Azure.AI.Agents.Persistent;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpeAzureAInAI.Extensions;

/// <summary>
/// Unit testing of <see cref="Microsoft.SemanticKernel.Agents.AzureAI.KernelFunctionExtensions"/>.
/// </summary>
public class KernelFunctionExtensionsTests
{
    /// <summary>
    /// Verify conversion from <see cref="KernelFunction"/> to <see cref="FunctionToolDefinition"/>.
    /// </summary>
    [Fact]
    public void VerifyKernelFunctionToFunctionTool()
    {
        // Arrange
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<TestPlugin>();

        // Assert
        Assert.Equal(2, plugin.FunctionCount);

        // Arrange
        KernelFunction f1 = plugin[nameof(TestPlugin.TestFunction1)];
        KernelFunction f2 = plugin[nameof(TestPlugin.TestFunction2)];

        // Act
        FunctionToolDefinition definition1 = f1.ToToolDefinition("testplugin");

        // Assert
        Assert.StartsWith($"testplugin-{nameof(TestPlugin.TestFunction1)}", definition1.Name, StringComparison.Ordinal);
        Assert.Equal("test description", definition1.Description);

        // Act
        FunctionToolDefinition definition2 = f2.ToToolDefinition("testplugin");

        // Assert
        Assert.StartsWith($"testplugin-{nameof(TestPlugin.TestFunction2)}", definition2.Name, StringComparison.Ordinal);
        Assert.Equal("test description", definition2.Description);
    }

    /// <summary>
    /// Exists only for parsing.
    /// </summary>
#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class TestPlugin()
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        [KernelFunction]
        [Description("test description")]
        public void TestFunction1() { }

        [KernelFunction]
        [Description("test description")]
#pragma warning disable IDE0060 // Unused parameter for mock kernel function
        public void TestFunction2(string p1, bool p2, int p3, string[] p4, ConsoleColor p5, DateTime p6) { }
#pragma warning restore IDE0060 // Unused parameter
    }
}
