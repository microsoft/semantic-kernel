// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelExtensionsTests
{
    [Fact]
    public void CreatePluginFromFunctions()
    {
        Kernel kernel = new();

        KernelPlugin plugin = kernel.CreatePluginFromFunctions("coolplugin", new[]
        {
            kernel.CreateFunctionFromMethod(() => { }, "Function1"),
            kernel.CreateFunctionFromMethod(() => { }, "Function2"),
        });

        Assert.NotNull(plugin);
        Assert.Empty(kernel.Plugins);

        Assert.Equal("coolplugin", plugin.Name);
        Assert.Empty(plugin.Description);
        Assert.Equal(2, plugin.FunctionCount);
        Assert.True(plugin.Contains("Function1"));
        Assert.True(plugin.Contains("Function2"));
    }

    [Fact]
    public void CreateEmptyPluginFromFunctions()
    {
        Kernel kernel = new();

        KernelPlugin plugin = kernel.CreatePluginFromFunctions("coolplugin");

        Assert.NotNull(plugin);
        Assert.Empty(kernel.Plugins);

        Assert.Equal("coolplugin", plugin.Name);
        Assert.Empty(plugin.Description);
        Assert.Empty(plugin);
        Assert.Equal(0, plugin.FunctionCount);
    }

    [Fact]
    public void CreatePluginFromDescriptionAndFunctions()
    {
        Kernel kernel = new();

        KernelPlugin plugin = kernel.CreatePluginFromFunctions("coolplugin", "the description", new[]
        {
            kernel.CreateFunctionFromMethod(() => { }, "Function1"),
            kernel.CreateFunctionFromMethod(() => { }, "Function2"),
        });

        Assert.NotNull(plugin);
        Assert.Empty(kernel.Plugins);

        Assert.Equal("coolplugin", plugin.Name);
        Assert.Equal("the description", plugin.Description);
        Assert.Equal(2, plugin.FunctionCount);
        Assert.True(plugin.Contains("Function1"));
        Assert.True(plugin.Contains("Function2"));
    }

    [Fact]
    public void ImportPluginFromFunctions()
    {
        Kernel kernel = new();

        kernel.ImportPluginFromFunctions("coolplugin", new[]
        {
            kernel.CreateFunctionFromMethod(() => { }, "Function1"),
            kernel.CreateFunctionFromMethod(() => { }, "Function2"),
        });

        Assert.Single(kernel.Plugins);

        KernelPlugin plugin = kernel.Plugins["coolplugin"];
        Assert.Equal("coolplugin", plugin.Name);
        Assert.Empty(plugin.Description);
        Assert.NotNull(plugin);

        Assert.Equal(2, plugin.FunctionCount);
        Assert.True(plugin.Contains("Function1"));
        Assert.True(plugin.Contains("Function2"));
    }

    [Fact]
    public void ImportPluginFromDescriptionAndFunctions()
    {
        Kernel kernel = new();

        kernel.ImportPluginFromFunctions("coolplugin", "the description", new[]
        {
            kernel.CreateFunctionFromMethod(() => { }, "Function1"),
            kernel.CreateFunctionFromMethod(() => { }, "Function2"),
        });

        Assert.Single(kernel.Plugins);

        KernelPlugin plugin = kernel.Plugins["coolplugin"];
        Assert.Equal("coolplugin", plugin.Name);
        Assert.Equal("the description", plugin.Description);
        Assert.NotNull(plugin);

        Assert.Equal(2, plugin.FunctionCount);
        Assert.True(plugin.Contains("Function1"));
        Assert.True(plugin.Contains("Function2"));
    }

    [Fact]
    public void AddFromFunctions()
    {
        Kernel kernel = new();

        kernel.Plugins.AddFromFunctions("coolplugin", new[]
        {
            kernel.CreateFunctionFromMethod(() => { }, "Function1"),
            kernel.CreateFunctionFromMethod(() => { }, "Function2"),
        });

        Assert.Single(kernel.Plugins);

        KernelPlugin plugin = kernel.Plugins["coolplugin"];
        Assert.Equal("coolplugin", plugin.Name);
        Assert.Empty(plugin.Description);
        Assert.NotNull(plugin);

        Assert.Equal(2, plugin.FunctionCount);
        Assert.True(plugin.Contains("Function1"));
        Assert.True(plugin.Contains("Function2"));
    }

    [Fact]
    public void AddFromDescriptionAndFunctions()
    {
        Kernel kernel = new();

        kernel.Plugins.AddFromFunctions("coolplugin", "the description", new[]
        {
            kernel.CreateFunctionFromMethod(() => { }, "Function1"),
            kernel.CreateFunctionFromMethod(() => { }, "Function2"),
        });

        Assert.Single(kernel.Plugins);

        KernelPlugin plugin = kernel.Plugins["coolplugin"];
        Assert.Equal("coolplugin", plugin.Name);
        Assert.Equal("the description", plugin.Description);
        Assert.NotNull(plugin);

        Assert.Equal(2, plugin.FunctionCount);
        Assert.True(plugin.Contains("Function1"));
        Assert.True(plugin.Contains("Function2"));
    }
}
