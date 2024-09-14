// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;
using KernelExtensions = Microsoft.SemanticKernel.Agents.OpenAI;

namespace SemanticKernel.Agents.UnitTests.OpenAI.Extensions;

/// <summary>
/// Unit testing of <see cref="KernelExtensions"/>.
/// </summary>
public class KernelExtensionsTests
{
    /// <summary>
    /// Verify function lookup using KernelExtensions.
    /// </summary>
    [Fact]
    public void VerifyGetKernelFunctionLookup()
    {
        // Arrange
        Kernel kernel = new();
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<TestPlugin>();
        kernel.Plugins.Add(plugin);

        // Act
        KernelFunction function = kernel.GetKernelFunction($"{nameof(TestPlugin)}-{nameof(TestPlugin.TestFunction)}", '-');

        // Assert
        Assert.NotNull(function);
        Assert.Equal(nameof(TestPlugin.TestFunction), function.Name);
    }

    /// <summary>
    /// Verify error case for function lookup using KernelExtensions.
    /// </summary>
    [Fact]
    public void VerifyGetKernelFunctionInvalid()
    {
        // Arrange
        Kernel kernel = new();
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<TestPlugin>();
        kernel.Plugins.Add(plugin);

        // Act and Assert
        Assert.Throws<KernelException>(() => kernel.GetKernelFunction("a", '-'));
        Assert.Throws<KernelException>(() => kernel.GetKernelFunction("a-b", ':'));
        Assert.Throws<KernelException>(() => kernel.GetKernelFunction("a-b-c", '-'));
    }

    /// <summary>
    /// Exists only for parsing.
    /// </summary>
#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class TestPlugin()
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        [KernelFunction]
        public void TestFunction() { }
    }
}
