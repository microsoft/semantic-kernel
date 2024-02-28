// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
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
    public void ItExposesFunctionsItContains()
    {
        KernelFunction func1 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function1");
        KernelFunction func2 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function2");

        KernelPlugin plugin = KernelPluginFactory.CreateFromFunctions("name", "description", new[] { func1, func2 });

        foreach (KernelFunction func in new[] { func1, func2 })
        {
            Assert.True(plugin.Contains(func.Name));
            Assert.True(plugin.Contains(func));

            Assert.True(plugin.TryGetFunction(func.Name, out KernelFunction? found));
            Assert.Equal(found, func);

            Assert.Equal(func, plugin[func.Name]);
            Assert.Equal(func, plugin[func.Name.ToUpperInvariant()]);
        }

        KernelFunction[] actual = plugin.OrderBy(f => f.Name).ToArray();
        Assert.Equal(actual[0], func1);
        Assert.Equal(actual[1], func2);

        Assert.Throws<KeyNotFoundException>(() => plugin["Function3"]);
        Assert.False(plugin.TryGetFunction("Function3", out KernelFunction? notFound));
        Assert.Null(notFound);
    }

    [Fact]
    public void ItContainsAddedFunctions()
    {
        KernelFunction func1 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function1");
        KernelFunction func2 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function2");

        KernelPlugin plugin = KernelPluginFactory.CreateFromFunctions("name", "description", new[] { func1, func2 });
        Assert.Equal(2, plugin.FunctionCount);

        Assert.True(plugin.TryGetFunction(func1.Name, out _));
        Assert.Equal(func1, plugin[func1.Name]);

        Assert.True(plugin.TryGetFunction(func2.Name, out _));
        Assert.Equal(func2, plugin[func2.Name]);
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
}
