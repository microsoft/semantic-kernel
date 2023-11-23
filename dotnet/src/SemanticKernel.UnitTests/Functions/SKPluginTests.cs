// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class SKPluginTests
{
    [Fact]
    public void ItRoundTripsCtorArguments()
    {
        SKPlugin plugin;

        var functions = new[]
        {
            SKFunctionFactory.CreateFromMethod(() => { }, "Function1"),
            SKFunctionFactory.CreateFromMethod(() => { }, "Function2"),
            SKFunctionFactory.CreateFromMethod(() => { }, "Function3"),
        };

        plugin = new SKPlugin("name");
        Assert.Equal("name", plugin.Name);
        Assert.Equal("", plugin.Description);
        Assert.Equal(0, plugin.FunctionCount);

        plugin = new SKPlugin("name", functions);
        Assert.Equal("name", plugin.Name);
        Assert.Equal("", plugin.Description);
        Assert.Equal(3, plugin.FunctionCount);
        Assert.All(functions, f => Assert.True(plugin.Contains(f)));

        plugin = new SKPlugin("name", "description");
        Assert.Equal("name", plugin.Name);
        Assert.Equal("description", plugin.Description);
        Assert.Equal(0, plugin.FunctionCount);

        plugin = new SKPlugin("name", "description", functions);
        Assert.Equal("name", plugin.Name);
        Assert.Equal("description", plugin.Description);
        Assert.Equal(3, plugin.FunctionCount);
        Assert.All(functions, f => Assert.True(plugin.Contains(f)));
    }

    [Fact]
    public void ItExposesFunctionsItContains()
    {
        KernelFunction func1 = SKFunctionFactory.CreateFromMethod(() => { }, "Function1");
        KernelFunction func2 = SKFunctionFactory.CreateFromMethod(() => { }, "Function2");

        SKPlugin plugin = new("name", new[] { func1, func2 });

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
        KernelFunction func1 = SKFunctionFactory.CreateFromMethod(() => { }, "Function1");
        KernelFunction func2 = SKFunctionFactory.CreateFromMethod(() => { }, "Function2");

        SKPlugin plugin = new("name");
        Assert.Equal(0, plugin.FunctionCount);

        plugin.AddFunction(func1);
        Assert.Equal(1, plugin.FunctionCount);
        Assert.True(plugin.TryGetFunction(func1.Name, out _));
        Assert.Equal(func1, plugin[func1.Name]);

        plugin.AddFunction(func2);
        Assert.Equal(2, plugin.FunctionCount);
        Assert.True(plugin.TryGetFunction(func2.Name, out _));
        Assert.Equal(func2, plugin[func2.Name]);

        Assert.Throws<ArgumentException>(() => plugin.AddFunction(func1));
        Assert.Throws<ArgumentException>(() => plugin.AddFunction(SKFunctionFactory.CreateFromMethod(() => { }, "function1")));
        Assert.Throws<ArgumentException>(() => plugin.AddFunction(SKFunctionFactory.CreateFromMethod(() => { }, "FUNCTION2")));
    }

    [Fact]
    public void ItThrowsForInvalidArguments()
    {
        Assert.Throws<ArgumentNullException>(() => new SKPlugin(null!));
        Assert.Throws<ArgumentNullException>(() => new SKPlugin(null!, ""));
        Assert.Throws<ArgumentNullException>(() => new SKPlugin(null!, "", Array.Empty<KernelFunction>()));
        Assert.Throws<ArgumentNullException>(() => new SKPlugin("name", "", new KernelFunction[] { null! }));

        SKPlugin plugin = new("name");
        Assert.Throws<ArgumentNullException>(() => plugin.AddFunction(null!));
        Assert.Throws<ArgumentNullException>(() => plugin.AddFunctions(null!));
        Assert.Throws<ArgumentNullException>(() => plugin[null!]);
        Assert.Throws<ArgumentNullException>(() => plugin.TryGetFunction(null!, out _));
        Assert.Throws<ArgumentNullException>(() => plugin.Contains((string)null!));
        Assert.Throws<ArgumentNullException>(() => plugin.Contains((KernelFunction)null!));
        Assert.Throws<ArgumentNullException>(() => ((ISKPlugin)null!).Contains("functionName"));
    }
}
