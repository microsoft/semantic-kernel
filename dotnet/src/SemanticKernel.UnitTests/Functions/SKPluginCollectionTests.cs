// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel;
using Xunit;

#pragma warning disable xUnit2013 // Do not use equality check to check for collection size.
#pragma warning disable xUnit2017 // Do not use Contains() to check if a value exists in a collection

namespace SemanticKernel.UnitTests.Functions;

public class SKPluginCollectionTests
{
    [Fact]
    public void ItHasExpectedDefaultValues()
    {
        SKPluginCollection c;

        c = new();
        Assert.Equal(0, c.Count);
        Assert.NotNull(c.GetEnumerator());
        Assert.False(c.GetEnumerator().MoveNext());

        c = new(Array.Empty<SKPlugin>());
        Assert.Equal(0, c.Count);
        Assert.NotNull(c.GetEnumerator());
        Assert.False(c.GetEnumerator().MoveNext());

        c = new(new[] { new SKPlugin("Function1") });
        Assert.Equal(1, c.Count);
        Assert.NotNull(c.GetEnumerator());
        Assert.True(c.Contains("function1"));
        Assert.False(c.Contains("function2"));

        c = new(new[] { new SKPlugin("Function1"), new SKPlugin("Function2") });
        Assert.Equal(2, c.Count);
        Assert.NotNull(c.GetEnumerator());
        Assert.True(c.Contains("function1"));
        Assert.True(c.Contains("function2"));
        Assert.False(c.Contains("function3"));

        c = new(new[] { new SKPlugin("Function1"), new SKPlugin("Function2") }.Select(p => p));
        Assert.Equal(2, c.Count);
        Assert.NotNull(c.GetEnumerator());
        Assert.True(c.Contains("function1"));
        Assert.True(c.Contains("function2"));
        Assert.False(c.Contains("function3"));

        c = new(c);
        Assert.Equal(2, c.Count);
        Assert.NotNull(c.GetEnumerator());
        Assert.True(c.Contains("function1"));
        Assert.True(c.Contains("function2"));
        Assert.False(c.Contains("function3"));
    }

    [Fact]
    public void ItExposesAddedPlugins()
    {
        var c = new SKPluginCollection();

        SKPlugin plugin1 = new("name1", new[]
        {
            SKFunction.FromMethod(() => { }, "Function1"),
            SKFunction.FromMethod(() => { }, "Function2"),
        });
        SKPlugin plugin2 = new("name2", new[]
        {
            SKFunction.FromMethod(() => { }, "Function3"),
        });

        c.Add(plugin1);
        Assert.Equal(1, c.Count);
        Assert.True(c.Contains(plugin1));
        Assert.True(c.Contains(plugin1.Name));
        Assert.True(c.Contains(plugin1.Name.ToUpperInvariant()));
        Assert.Equal(plugin1, c[plugin1.Name]);
        Assert.False(c.Contains(plugin2));
        Assert.False(c.Contains(plugin2.Name));
        Assert.False(c.Contains(plugin2.Name.ToUpperInvariant()));
        Assert.Equal(new[] { plugin1 }, c.ToArray());

        c.Add(plugin2);
        Assert.Equal(2, c.Count);
        Assert.True(c.Contains(plugin1));
        Assert.True(c.Contains(plugin1.Name));
        Assert.True(c.Contains(plugin1.Name.ToUpperInvariant()));
        Assert.Equal(plugin1, c[plugin1.Name]);
        Assert.True(c.Contains(plugin2));
        Assert.True(c.Contains(plugin2.Name));
        Assert.True(c.Contains(plugin2.Name.ToUpperInvariant()));
        Assert.Equal(plugin2, c[plugin2.Name]);
        Assert.Equal(new[] { plugin1, plugin2 }, c.OrderBy(f => f.Name, StringComparer.OrdinalIgnoreCase).ToArray());

        Assert.True(c.Remove(plugin1));
        Assert.False(c.Remove(plugin1));
        Assert.Equal(1, c.Count);
        Assert.False(c.Contains(plugin1));
        Assert.False(c.Contains(plugin1.Name));
        Assert.False(c.Contains(plugin1.Name.ToUpperInvariant()));
        Assert.True(c.Contains(plugin2));
        Assert.True(c.Contains(plugin2.Name));
        Assert.True(c.Contains(plugin2.Name.ToUpperInvariant()));
        Assert.Equal(plugin2, c[plugin2.Name]);
        Assert.Equal(new[] { plugin2 }, c.ToArray());

        Assert.True(c.Remove(plugin2));
        Assert.False(c.Remove(plugin2));
        Assert.Equal(0, c.Count);
        Assert.False(c.Contains(plugin1));
        Assert.False(c.Contains(plugin1.Name));
        Assert.False(c.Contains(plugin1.Name.ToUpperInvariant()));
        Assert.False(c.Contains(plugin2));
        Assert.False(c.Contains(plugin2.Name));
        Assert.False(c.Contains(plugin2.Name.ToUpperInvariant()));
        Assert.Equal(Array.Empty<ISKPlugin>(), c.ToArray());

        c.Add(plugin2);
        Assert.Equal(1, c.Count);
        c.Clear();
        Assert.Equal(0, c.Count);
    }

    [Fact]
    public void ItExposesGroupsOfAddedPlugins()
    {
        var c = new SKPluginCollection();

        c.AddRange(new[] { new SKPlugin("name1"), new SKPlugin("name2") });
        Assert.Equal(2, c.Count);
        Assert.Equal("name1", c["name1"].Name);
        Assert.Equal("name2", c["name2"].Name);
    }

    [Fact]
    public void ItExposesFunctionViewsOfAllFunctions()
    {
        var c = new SKPluginCollection()
        {
            new SKPlugin("plugin1", new[]
            {
                SKFunction.FromMethod(() => { }, "Function1"),
                SKFunction.FromMethod(() => { }, "Function2"),
            }),
            new SKPlugin("plugin2", new[]
            {
                SKFunction.FromMethod(() => { }, "Function2"),
                SKFunction.FromMethod(() => { }, "Function3"),
            })
        };

        IList<SKFunctionMetadata> views = c.GetFunctionsMetadata().OrderBy(f => f.Name).ToList();

        Assert.Equal("plugin1", views[0].PluginName);
        Assert.Equal("Function1", views[0].Name);

        Assert.Equal("plugin1", views[1].PluginName);
        Assert.Equal("Function2", views[1].Name);

        Assert.Equal("plugin2", views[2].PluginName);
        Assert.Equal("Function2", views[2].Name);

        Assert.Equal("plugin2", views[3].PluginName);
        Assert.Equal("Function3", views[3].Name);
    }

    [Fact]
    public void ItExposesFunctionsInPlugins()
    {
        SKPlugin plugin1 = new("name1", new[]
        {
            SKFunction.FromMethod(() => { }, "Function1"),
            SKFunction.FromMethod(() => { }, "Function2"),
        });
        SKPlugin plugin2 = new("name2", new[]
        {
            SKFunction.FromMethod(() => { }, "Function3"),
        });

        var c = new SKPluginCollection(new[] { plugin1, plugin2 });

        Assert.Same(plugin1["Function1"], c.GetFunction("name1", "Function1"));
        Assert.Same(plugin1["Function2"], c.GetFunction("name1", "Function2"));
        Assert.Same(plugin2["Function3"], c.GetFunction("name2", "Function3"));
        Assert.Throws<KeyNotFoundException>(() => c.GetFunction("name1", "Function0"));
        Assert.Throws<KeyNotFoundException>(() => c.GetFunction("name2", "Function1"));
        Assert.Throws<KeyNotFoundException>(() => c.GetFunction("name3", "Function1"));

        Assert.Same(plugin1["Function1"], c.GetFunction(null, "Function1"));
        Assert.Same(plugin1["Function2"], c.GetFunction(null, "Function2"));
        Assert.Same(plugin2["Function3"], c.GetFunction(null, "Function3"));

        Assert.True(c.TryGetFunction("name1", "Function1", out ISKFunction? func));
        Assert.Same(plugin1["Function1"], func);

        Assert.False(c.TryGetFunction("name2", "Function1", out func));
        Assert.Null(func);

        Assert.True(c.TryGetFunction(null, "Function3", out func));
        Assert.Same(plugin2["Function3"], func);
    }

    [Fact]
    public void ItThrowsForInvalidArguments()
    {
        Assert.Throws<ArgumentNullException>(() => new SKPluginCollection(null!));
        Assert.Throws<ArgumentNullException>(() => new SKPluginCollection(new ISKPlugin[] { null! }));

        SKPluginCollection c = new();
        Assert.Throws<ArgumentNullException>(() => c.Add(null!));
        Assert.Throws<ArgumentNullException>(() => c.Remove(null!));
        Assert.Throws<ArgumentNullException>(() => c.Contains(null!));
        Assert.Throws<ArgumentNullException>(() => c[null!]);
        Assert.Throws<ArgumentNullException>(() => c.TryGetPlugin(null!, out _));
        Assert.Throws<ArgumentNullException>(() => ((ICollection<ISKPlugin>)c).CopyTo(null!, 0));

        Assert.Throws<KeyNotFoundException>(() => c["Function1"]);
    }

    [Fact]
    public void ItCopiesToDestinationArrayInCopyTo()
    {
        ISKPlugin plugin1 = new SKPlugin("plugin1");
        ISKPlugin plugin2 = new SKPlugin("plugin2");
        ICollection<ISKPlugin> c = new SKPluginCollection(new[] { plugin1, plugin2 });

        var array = new ISKPlugin[4];

        c.CopyTo(array, 0);
        Assert.Same(plugin1, array[0]);
        Assert.Same(plugin2, array[1]);
        Assert.Null(array[2]);
        Assert.Null(array[3]);

        Array.Clear(array, 0, array.Length);
        c.CopyTo(array, 1);
        Assert.Same(plugin1, array[1]);
        Assert.Same(plugin2, array[2]);
        Assert.Null(array[0]);
        Assert.Null(array[3]);

        Array.Clear(array, 0, array.Length);
        c.CopyTo(array, 2);
        Assert.Same(plugin1, array[2]);
        Assert.Same(plugin2, array[3]);
        Assert.Null(array[0]);
        Assert.Null(array[1]);

        Assert.Throws<ArgumentOutOfRangeException>(() => c.CopyTo(array, -1));
        Assert.Throws<ArgumentException>(() => c.CopyTo(array, 3));
        Assert.Throws<ArgumentException>(() => c.CopyTo(array, 4));
    }
}
