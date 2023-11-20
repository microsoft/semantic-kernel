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
            SKFunction.FromMethod(() => { }, "Function1"),
            SKFunction.FromMethod(() => { }, "Function2"),
            SKFunction.FromMethod(() => { }, "Function3"),
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
        ISKFunction func1 = SKFunction.FromMethod(() => { }, "Function1");
        ISKFunction func2 = SKFunction.FromMethod(() => { }, "Function2");

        SKPlugin plugin = new("name", new[] { func1, func2 });

        foreach (ISKFunction func in new[] { func1, func2 })
        {
            Assert.True(plugin.Contains(func.Name));
            Assert.True(plugin.Contains(func));

            Assert.True(plugin.TryGetFunction(func.Name, out ISKFunction? found));
            Assert.Equal(found, func);

            Assert.Equal(func, plugin[func.Name]);
            Assert.Equal(func, plugin[func.Name.ToUpperInvariant()]);
        }

        ISKFunction[] actual = plugin.OrderBy(f => f.Name).ToArray();
        Assert.Equal(actual[0], func1);
        Assert.Equal(actual[1], func2);

        Assert.Throws<KeyNotFoundException>(() => plugin["Function3"]);
        Assert.False(plugin.TryGetFunction("Function3", out ISKFunction? notFound));
        Assert.Null(notFound);
    }

    [Fact]
    public void ItContainsAddedFunctions()
    {
        ISKFunction func1 = SKFunction.FromMethod(() => { }, "Function1");
        ISKFunction func2 = SKFunction.FromMethod(() => { }, "Function2");

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
        Assert.Throws<ArgumentException>(() => plugin.AddFunction(SKFunction.FromMethod(() => { }, "function1")));
        Assert.Throws<ArgumentException>(() => plugin.AddFunction(SKFunction.FromMethod(() => { }, "FUNCTION2")));
    }

    [Fact]
    public void ItThrowsForInvalidArguments()
    {
        Assert.Throws<ArgumentNullException>(() => new SKPlugin(null!));
        Assert.Throws<ArgumentNullException>(() => new SKPlugin(null!, ""));
        Assert.Throws<ArgumentNullException>(() => new SKPlugin(null!, "", Array.Empty<ISKFunction>()));
        Assert.Throws<ArgumentNullException>(() => new SKPlugin("name", "", new ISKFunction[] { null! }));

        SKPlugin plugin = new("name");
        Assert.Throws<ArgumentNullException>(() => plugin.AddFunction(null!));
        Assert.Throws<ArgumentNullException>(() => plugin.AddFunctions(null!));
        Assert.Throws<ArgumentNullException>(() => plugin[null!]);
        Assert.Throws<ArgumentNullException>(() => plugin.TryGetFunction(null!, out _));
        Assert.Throws<ArgumentNullException>(() => plugin.Contains((string)null!));
        Assert.Throws<ArgumentNullException>(() => plugin.Contains((ISKFunction)null!));
        Assert.Throws<ArgumentNullException>(() => ((ISKPlugin)null!).Contains("functionName"));
    }
}
