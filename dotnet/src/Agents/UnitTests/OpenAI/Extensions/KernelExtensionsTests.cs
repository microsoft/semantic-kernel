// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI.Extensions;
using Xunit;
using KernelExtensions = Microsoft.SemanticKernel.Agents.OpenAI.Extensions;

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
        Kernel kernel = Kernel.CreateBuilder().Build();
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<TestPlugin>();
        kernel.Plugins.Add(plugin);

        KernelFunction function = kernel.GetKernelFunction($"{nameof(TestPlugin)}-{nameof(TestPlugin.TestFunction)}", '-');
        Assert.NotNull(function);
        Assert.Equal(nameof(TestPlugin.TestFunction), function.Name);
    }

    /// <summary>
    /// Verify error case for function lookup using KernelExtensions.
    /// </summary>
    [Fact]
    public void VerifyGetKernelFunctionInvalid()
    {
        Kernel kernel = Kernel.CreateBuilder().Build();
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<TestPlugin>();
        kernel.Plugins.Add(plugin);

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
