// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
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
            KernelFunctionFactory.CreateFromPrompt("some prompt", functionName: "Function3"),
        };

        Assert.Equal("Function1", functions[0].ToString());
        Assert.Equal("Function2", functions[1].ToString());
        Assert.Equal("Function3", functions[2].ToString());

        plugin = KernelPluginFactory.CreateFromFunctions("name", null, null);
        Assert.Equal("name", plugin.Name);
        Assert.Equal("", plugin.Description);
        Assert.Equal(0, plugin.FunctionCount);

        plugin = KernelPluginFactory.CreateFromFunctions("name", "", functions);
        Assert.Equal("name", plugin.Name);
        Assert.Equal("", plugin.Description);
        Assert.Equal(3, plugin.FunctionCount);
        Assert.All(functions, f => Assert.True(plugin.Contains(f)));

        Assert.Equal("name.Function1", plugin["Function1"].ToString());
        Assert.Equal("name.Function2", plugin["Function2"].ToString());
        Assert.Equal("name.Function3", plugin["Function3"].ToString());

        plugin = KernelPluginFactory.CreateFromFunctions("name", "description");
        Assert.Equal("name", plugin.Name);
        Assert.Equal("description", plugin.Description);
        Assert.Equal(0, plugin.FunctionCount);

        plugin = KernelPluginFactory.CreateFromFunctions("name", "description", functions);
        Assert.Equal("name", plugin.Name);
        Assert.Equal("description", plugin.Description);
        Assert.Equal(3, plugin.FunctionCount);
        Assert.All(functions, f => Assert.True(plugin.Contains(f)));

        Assert.Equal("name.Function1", plugin["Function1"].ToString());
        Assert.Equal("name.Function2", plugin["Function2"].ToString());
        Assert.Equal("name.Function3", plugin["Function3"].ToString());
    }

    [Fact]
    public async Task ItExposesFunctionsItContainsAsync()
    {
        var kernel = new Kernel();
        KernelFunction func1 = KernelFunctionFactory.CreateFromMethod(() => "Return1", "Function1");
        KernelFunction func2 = KernelFunctionFactory.CreateFromMethod(() => "Return2", "Function2");

        KernelPlugin plugin = KernelPluginFactory.CreateFromFunctions("name", "description", [func1, func2]);

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

        KernelPlugin plugin = KernelPluginFactory.CreateFromFunctions("name", "description", [func1, func2]);
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

        IList<KernelFunctionMetadata> metadata = KernelPluginFactory.CreateFromFunctions("plugin2", "description1",
        [
            KernelFunctionFactory.CreateFromMethod(() => { }, "Function1"),
            KernelFunctionFactory.CreateFromMethod(() => { }, "Function2"),
        ]).GetFunctionsMetadata();

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
        Assert.Throws<ArgumentNullException>(() => KernelPluginFactory.CreateFromFunctions(null!, "", []));
        Assert.Throws<ArgumentNullException>(() => KernelPluginFactory.CreateFromFunctions("name", "", [null!]));

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

        KernelPlugin plugin1 = KernelPluginFactory.CreateFromFunctions("Plugin1", "Description", [func1]);
        Assert.Equal(1, plugin1.FunctionCount);
        KernelPlugin plugin2 = KernelPluginFactory.CreateFromFunctions("Plugin1", "Description", [func1]);
        Assert.Equal(1, plugin2.FunctionCount);

        Assert.True(plugin1.TryGetFunction(func1.Name, out KernelFunction? pluginFunc1));
        Assert.NotEqual(func1, pluginFunc1);
        Assert.Equal(plugin1.Name, pluginFunc1.PluginName);

        Assert.True(plugin2.TryGetFunction(func1.Name, out KernelFunction? pluginFunc2));
        Assert.NotEqual(func1, pluginFunc2);
        Assert.Equal(plugin2.Name, pluginFunc2.PluginName);
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task ItCanProduceAIFunctionsThatInvokeKernelFunctions(bool withKernel)
    {
        string? actualArg1 = null;
        int? actualArg2 = null;
        double? actualArg3 = null;
        Kernel? actualKernel1 = null;
        Kernel? actualKernel2 = null;
        CancellationToken? actualToken1 = null;
        CancellationToken? actualToken2 = null;

        KernelPlugin plugin = KernelPluginFactory.CreateFromFunctions(
            "PluginName", [
                KernelFunctionFactory.CreateFromMethod((string arg1, Kernel kernel1, CancellationToken ct1) =>
                {
                    actualArg1 = arg1;
                    actualKernel1 = kernel1;
                    actualToken1 = ct1;
                    return "Return1";
                }, "Function1"),
                KernelFunctionFactory.CreateFromMethod((int arg2, double arg3, Kernel kernel2, CancellationToken ct2) =>
                {
                    actualArg2 = arg2;
                    actualArg3 = arg3;
                    actualKernel2 = kernel2;
                    actualToken2 = ct2;
                    return "Return2";
                }, "Function2"),
            ]);

        Kernel? kernel = withKernel ? new Kernel() : null;
        AIFunction[] funcs = plugin.AsAIFunctions(kernel).ToArray();
        Assert.Equal(2, funcs.Length);

        Assert.Equal("PluginName_Function1", funcs[0].Name);
        Assert.Equal("PluginName_Function2", funcs[1].Name);

        var func1Properties = funcs[0].JsonSchema.GetProperty("properties").EnumerateObject().ToArray();
        var func2Properties = funcs[1].JsonSchema.GetProperty("properties").EnumerateObject().ToArray();
        Assert.Equal("arg1", Assert.Single(func1Properties).Name);
        Assert.Equal(2, func2Properties.Length);
        Assert.Equal("arg2", func2Properties[0].Name);
        Assert.Equal("arg3", func2Properties[1].Name);

        Assert.Equal(plugin["Function1"].Metadata.Parameters[0].Schema?.ToString(), JsonSerializer.Serialize(func1Properties[0].Value));
        Assert.Equal(plugin["Function2"].Metadata.Parameters[0].Schema?.ToString(), JsonSerializer.Serialize(func2Properties[0].Value));
        Assert.Equal(plugin["Function2"].Metadata.Parameters[1].Schema?.ToString(), JsonSerializer.Serialize(func2Properties[1].Value));

        using CancellationTokenSource cts = new();

        JsonElement return1 = Assert.IsType<JsonElement>(await funcs[0].InvokeAsync(
            new(new Dictionary<string, object?>([KeyValuePair.Create("arg1", (object?)"value1")])),
            cts.Token));
        Assert.Equal("Return1", return1.ToString());

        JsonElement return2 = Assert.IsType<JsonElement>(await funcs[1].InvokeAsync(
            new(new Dictionary<string, object?>([KeyValuePair.Create("arg2", (object?)42), KeyValuePair.Create("arg3", (object?)84.0)])),
            cts.Token));
        Assert.Equal("Return2", return2.ToString());

        Assert.Equal("value1", actualArg1);
        Assert.Equal(42, actualArg2);
        Assert.Equal(84.0, actualArg3);

        Assert.NotNull(actualKernel1);
        Assert.NotNull(actualKernel2);
        Assert.Equal(withKernel, ReferenceEquals(actualKernel1, kernel));
        Assert.Equal(withKernel, ReferenceEquals(actualKernel2, kernel));

        Assert.Equal(cts.Token, actualToken1);
        Assert.Equal(cts.Token, actualToken2);
    }
}
