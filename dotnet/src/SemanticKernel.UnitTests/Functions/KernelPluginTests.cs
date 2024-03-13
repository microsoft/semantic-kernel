// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelPluginTests
{
    [Fact]
    public void ItRoundTripsCtorArguments()
    {
        KernelPlugin plugin;

        var functions = new[]
        {
            KernelFunctionFactory.CreateFromMethod(() => { }, "Function1"),
            KernelFunctionFactory.CreateFromMethod(() => { }, "Function2"),
            KernelFunctionFactory.CreateFromMethod(() => { }, "Function3"),
        };

        plugin = KernelPluginFactory.CreateFromFunctions("name", null, null);
        Assert.Equal("name", plugin.Name);
        Assert.Equal("", plugin.Description);
        Assert.Equal(0, plugin.FunctionCount);

        plugin = KernelPluginFactory.CreateFromFunctions("name", "", functions);
        Assert.Equal("name", plugin.Name);
        Assert.Equal("", plugin.Description);
        Assert.Equal(3, plugin.FunctionCount);
        Assert.All(functions, f => Assert.True(plugin.Contains(f)));

        plugin = KernelPluginFactory.CreateFromFunctions("name", "description");
        Assert.Equal("name", plugin.Name);
        Assert.Equal("description", plugin.Description);
        Assert.Equal(0, plugin.FunctionCount);

        plugin = KernelPluginFactory.CreateFromFunctions("name", "description", functions);
        Assert.Equal("name", plugin.Name);
        Assert.Equal("description", plugin.Description);
        Assert.Equal(3, plugin.FunctionCount);
        Assert.All(functions, f => Assert.True(plugin.Contains(f)));
    }

    [Fact]
    public async Task ItExposesFunctionsItContainsAsync()
    {
        var kernel = new Kernel();
        KernelFunction func1 = KernelFunctionFactory.CreateFromMethod(() => "Return1", "Function1");
        KernelFunction func2 = KernelFunctionFactory.CreateFromMethod(() => "Return2", "Function2");

        KernelPlugin plugin = KernelPluginFactory.CreateFromFunctions("name", "description", new[] { func1, func2 });

        foreach (KernelFunction func in new[] { func1, func2 })
        {
            Assert.True(plugin.Contains(func.Name));
            Assert.True(plugin.Contains(func));

            Assert.True(plugin.TryGetFunction(func.Name, out KernelFunction? found));
            Assert.Equal(found.Name, found.Name);

            Assert.Equal(func.Name, plugin[func.Name].Name);
            Assert.Equal(func.Name, plugin[func.Name.ToUpperInvariant()].Name);
        }

        KernelFunction[] actual = plugin.OrderBy(f => f.Name).ToArray();
        var result1 = await func1.InvokeAsync(kernel);
        var result2 = await actual[0].InvokeAsync(kernel);
        Assert.Equal(result1.ToString(), result2.ToString());
        var result3 = await func2.InvokeAsync(kernel);
        var result4 = await actual[1].InvokeAsync(kernel);
        Assert.Equal(result3.ToString(), result4.ToString());

        Assert.Throws<KeyNotFoundException>(() => plugin["Function3"]);
        Assert.False(plugin.TryGetFunction("Function3", out KernelFunction? notFound));
        Assert.Null(notFound);
    }

    [Fact]
    public async Task ItContainsAddedFunctionsAsync()
    {
        var kernel = new Kernel();
        KernelFunction func1 = KernelFunctionFactory.CreateFromMethod(() => "Return1", "Function1");
        KernelFunction func2 = KernelFunctionFactory.CreateFromMethod(() => "Return2", "Function2");

        KernelPlugin plugin = KernelPluginFactory.CreateFromFunctions("name", "description", new[] { func1, func2 });
        Assert.Equal(2, plugin.FunctionCount);

        Assert.True(plugin.TryGetFunction(func1.Name, out _));
        var result1 = await func1.InvokeAsync(kernel);
        var result2 = await plugin[func1.Name].InvokeAsync(kernel);
        Assert.Equal(result1.ToString(), result2.ToString());

        Assert.True(plugin.TryGetFunction(func2.Name, out _));
        var result3 = await func2.InvokeAsync(kernel);
        var result4 = await plugin[func2.Name].InvokeAsync(kernel);
        Assert.Equal(result3.ToString(), result4.ToString());
    }

    [Fact]
    public void ItExposesFunctionMetadataForAllFunctions()
    {
        Assert.Empty(KernelPluginFactory.CreateFromFunctions("plugin1").GetFunctionsMetadata());

        IList<KernelFunctionMetadata> metadata = KernelPluginFactory.CreateFromFunctions("plugin2", "description1", new[]
        {
            KernelFunctionFactory.CreateFromMethod(() => { }, "Function1"),
            KernelFunctionFactory.CreateFromMethod(() => { }, "Function2"),
        }).GetFunctionsMetadata();

        Assert.NotNull(metadata);
        Assert.Equal(2, metadata.Count);

        Assert.Equal("plugin2", metadata[0].PluginName);
        Assert.Equal("Function1", metadata[0].Name);

        Assert.Equal("plugin2", metadata[1].PluginName);
        Assert.Equal("Function2", metadata[1].Name);
    }

    [Fact]
    public void ItThrowsForInvalidArguments()
    {
        Assert.Throws<ArgumentNullException>(() => KernelPluginFactory.CreateFromFunctions(null!));
        Assert.Throws<ArgumentNullException>(() => KernelPluginFactory.CreateFromFunctions(null!, ""));
        Assert.Throws<ArgumentNullException>(() => KernelPluginFactory.CreateFromFunctions(null!, "", Array.Empty<KernelFunction>()));
        Assert.Throws<ArgumentNullException>(() => KernelPluginFactory.CreateFromFunctions("name", "", new KernelFunction[] { null! }));

        KernelPlugin plugin = KernelPluginFactory.CreateFromFunctions("name");
        Assert.Throws<ArgumentNullException>(() => plugin[null!]);
        Assert.Throws<ArgumentNullException>(() => plugin.TryGetFunction(null!, out _));
        Assert.Throws<ArgumentNullException>(() => plugin.Contains((string)null!));
        Assert.Throws<ArgumentNullException>(() => plugin.Contains((KernelFunction)null!));
    }

    [Fact]
    public void ItCanAddSameFunctionToTwoPlugins()
    {
        var kernel = new Kernel();
        KernelFunction func1 = KernelFunctionFactory.CreateFromMethod(() => "Return1", "Function1");

        KernelPlugin plugin1 = KernelPluginFactory.CreateFromFunctions("Plugin1", "Description", new[] { func1 });
        Assert.Equal(1, plugin1.FunctionCount);
        KernelPlugin plugin2 = KernelPluginFactory.CreateFromFunctions("Plugin1", "Description", new[] { func1 });
        Assert.Equal(1, plugin2.FunctionCount);

        Assert.True(plugin1.TryGetFunction(func1.Name, out KernelFunction? pluginFunc1));
        Assert.NotEqual(func1, pluginFunc1);
        Assert.Equal(plugin1.Name, pluginFunc1.PluginName);

        Assert.True(plugin2.TryGetFunction(func1.Name, out KernelFunction? pluginFunc2));
        Assert.NotEqual(func1, pluginFunc2);
        Assert.Equal(plugin2.Name, pluginFunc2.PluginName);
    }
}
