// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel;
using Xunit;

#pragma warning disable xUnit2013 // Do not use equality check to check for collection size.
#pragma warning disable xUnit2017 // Do not use Contains() to check if a value exists in a collection

namespace SemanticKernel.UnitTests.Functions;

public class KernelPluginCollectionTests
{
    [Fact]
    public void ItHasExpectedDefaultValues()
    {
        KernelPluginCollection c;

        c = new();
        Assert.Equal(0, c.Count);
        Assert.NotNull(c.GetEnumerator());
        Assert.False(c.GetEnumerator().MoveNext());

        c = new(Array.Empty<DefaultKernelPlugin>());
        Assert.Equal(0, c.Count);
        Assert.NotNull(c.GetEnumerator());
        Assert.False(c.GetEnumerator().MoveNext());

        c = new(new[] { KernelPluginFactory.CreateFromFunctions("plugin1") });
        Assert.Equal(1, c.Count);
        Assert.NotNull(c.GetEnumerator());
        Assert.True(c.Contains("plugin1"));
        Assert.False(c.Contains("plugin2"));

        c = new(new[] { KernelPluginFactory.CreateFromFunctions("plugin1"), KernelPluginFactory.CreateFromFunctions("plugin2") });
        Assert.Equal(2, c.Count);
        Assert.NotNull(c.GetEnumerator());
        Assert.True(c.Contains("plugin1"));
        Assert.True(c.Contains("plugin2"));
        Assert.False(c.Contains("plugin3"));

        c = new(new[] { KernelPluginFactory.CreateFromFunctions("plugin1"), KernelPluginFactory.CreateFromFunctions("plugin2") }.Select(p => p));
        Assert.Equal(2, c.Count);
        Assert.NotNull(c.GetEnumerator());
        Assert.True(c.Contains("plugin1"));
        Assert.True(c.Contains("plugin2"));
        Assert.False(c.Contains("plugin3"));

        c = new(c);
        Assert.Equal(2, c.Count);
        Assert.NotNull(c.GetEnumerator());
        Assert.True(c.Contains("plugin1"));
        Assert.True(c.Contains("plugin2"));
        Assert.False(c.Contains("plugin3"));
    }

    [Fact]
    public void ItExposesAddedPlugins()
    {
        var c = new KernelPluginCollection();

        DefaultKernelPlugin plugin1 = new("name1", "description1", new[]
        {
            KernelFunctionFactory.CreateFromMethod(() => { }, "Function1"),
            KernelFunctionFactory.CreateFromMethod(() => { }, "Function2"),
        });
        DefaultKernelPlugin plugin2 = new("name2", "description2", new[]
        {
            KernelFunctionFactory.CreateFromMethod(() => { }, "Function3"),
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
        Assert.Equal(Array.Empty<KernelPlugin>(), c.ToArray());

        c.Add(plugin2);
        Assert.Equal(1, c.Count);
        c.Clear();
        Assert.Equal(0, c.Count);
    }

    [Fact]
    public void ItExposesGroupsOfAddedPlugins()
    {
        var c = new KernelPluginCollection();

        c.AddRange(new[] { KernelPluginFactory.CreateFromFunctions("name1"), KernelPluginFactory.CreateFromFunctions("name2") });
        Assert.Equal(2, c.Count);
        Assert.Equal("name1", c["name1"].Name);
        Assert.Equal("name2", c["name2"].Name);
    }

    [Fact]
    public void ItExposesFunctionMetadataForAllFunctions()
    {
        var c = new KernelPluginCollection()
        {
            KernelPluginFactory.CreateFromFunctions("plugin1", "description1", new[]
            {
                KernelFunctionFactory.CreateFromMethod(() => { }, "Function1"),
                KernelFunctionFactory.CreateFromMethod(() => { }, "Function2"),
            }),
            KernelPluginFactory.CreateFromFunctions("plugin2", "description2", new[]
            {
                KernelFunctionFactory.CreateFromMethod(() => { }, "Function2"),
                KernelFunctionFactory.CreateFromMethod(() => { }, "Function3"),
            })
        };

        IList<KernelFunctionMetadata> metadata = c.GetFunctionsMetadata().OrderBy(f => f.Name).ToList();

        Assert.Equal("plugin1", metadata[0].PluginName);
        Assert.Equal("Function1", metadata[0].Name);

        Assert.Equal("plugin1", metadata[1].PluginName);
        Assert.Equal("Function2", metadata[1].Name);

        Assert.Equal("plugin2", metadata[2].PluginName);
        Assert.Equal("Function2", metadata[2].Name);

        Assert.Equal("plugin2", metadata[3].PluginName);
        Assert.Equal("Function3", metadata[3].Name);
    }

    [Fact]
    public void ItExposesFunctionsInPlugins()
    {
        DefaultKernelPlugin plugin1 = new("name1", "description1", new[]
        {
            KernelFunctionFactory.CreateFromMethod(() => { }, "Function1"),
            KernelFunctionFactory.CreateFromMethod(() => { }, "Function2"),
        });
        DefaultKernelPlugin plugin2 = new("name2", "description2", new[]
        {
            KernelFunctionFactory.CreateFromMethod(() => { }, "Function3"),
        });

        var c = new KernelPluginCollection(new[] { plugin1, plugin2 });

        Assert.Same(plugin1["Function1"], c.GetFunction("name1", "Function1"));
        Assert.Same(plugin1["Function2"], c.GetFunction("name1", "Function2"));
        Assert.Same(plugin2["Function3"], c.GetFunction("name2", "Function3"));
        Assert.Throws<KeyNotFoundException>(() => c.GetFunction("name1", "Function0"));
        Assert.Throws<KeyNotFoundException>(() => c.GetFunction("name2", "Function1"));
        Assert.Throws<KeyNotFoundException>(() => c.GetFunction("name3", "Function1"));

        Assert.Same(plugin1["Function1"], c.GetFunction(null, "Function1"));
        Assert.Same(plugin1["Function2"], c.GetFunction(null, "Function2"));
        Assert.Same(plugin2["Function3"], c.GetFunction(null, "Function3"));

        Assert.True(c.TryGetFunction("name1", "Function1", out KernelFunction? func));
        Assert.Same(plugin1["Function1"], func);

        Assert.False(c.TryGetFunction("name2", "Function1", out func));
        Assert.Null(func);

        Assert.True(c.TryGetFunction(null, "Function3", out func));
        Assert.Same(plugin2["Function3"], func);
    }

    [Fact]
    public void ItThrowsForInvalidArguments()
    {
        Assert.Throws<ArgumentNullException>(() => new KernelPluginCollection(null!));
        Assert.Throws<ArgumentNullException>(() => new KernelPluginCollection(new KernelPlugin[] { null! }));

        KernelPluginCollection c = new();
        Assert.Throws<ArgumentNullException>(() => c.Add(null!));
        Assert.Throws<ArgumentNullException>(() => c.Remove(null!));
        Assert.Throws<ArgumentNullException>(() => c.Contains(null!));
        Assert.Throws<ArgumentNullException>(() => c[null!]);
        Assert.Throws<ArgumentNullException>(() => c.TryGetPlugin(null!, out _));
        Assert.Throws<ArgumentNullException>(() => ((ICollection<KernelPlugin>)c).CopyTo(null!, 0));

        Assert.Throws<KeyNotFoundException>(() => c["Function1"]);
    }

    [Fact]
    public void ItCopiesToDestinationArrayInCopyTo()
    {
        KernelPlugin plugin1 = KernelPluginFactory.CreateFromFunctions("plugin1");
        KernelPlugin plugin2 = KernelPluginFactory.CreateFromFunctions("plugin2");
        ICollection<KernelPlugin> c = new KernelPluginCollection(new[] { plugin1, plugin2 });

        var array = new KernelPlugin[4];

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
