// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using SemanticKernel.UnitTests.Functions.JsonSerializerContexts;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelExtensionsCreateAddAImportPluginsTests
{
    private readonly Kernel _kernel = new();

    [Fact]
    public void AddFromFunctions()
    {
        this._kernel.Plugins.AddFromFunctions("coolplugin",
        [
            this._kernel.CreateFunctionFromMethod(() => { }, "Function1"),
            this._kernel.CreateFunctionFromMethod(() => { }, "Function2"),
        ]);

        Assert.Single(this._kernel.Plugins);

        KernelPlugin plugin = this._kernel.Plugins["coolplugin"];
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
        this._kernel.Plugins.AddFromFunctions("coolplugin", "the description",
        [
            this._kernel.CreateFunctionFromMethod(() => { }, "Function1"),
            this._kernel.CreateFunctionFromMethod(() => { }, "Function2"),
        ]);

        Assert.Single(this._kernel.Plugins);

        KernelPlugin plugin = this._kernel.Plugins["coolplugin"];
        Assert.Equal("coolplugin", plugin.Name);
        Assert.Equal("the description", plugin.Description);
        Assert.NotNull(plugin);

        Assert.Equal(2, plugin.FunctionCount);
        Assert.True(plugin.Contains("Function1"));
        Assert.True(plugin.Contains("Function2"));
    }

    [Fact]
    public void CreateEmptyPluginFromFunctions()
    {
        KernelPlugin plugin = this._kernel.CreatePluginFromFunctions("coolplugin");

        Assert.NotNull(plugin);
        Assert.Empty(this._kernel.Plugins);

        Assert.Equal("coolplugin", plugin.Name);
        Assert.Empty(plugin.Description);
        Assert.Empty(plugin);
        Assert.Equal(0, plugin.FunctionCount);
    }

    [Fact]
    public void CreatePluginFromDescriptionAndFunctions()
    {
        KernelPlugin plugin = this._kernel.CreatePluginFromFunctions("coolplugin", "the description",
        [
            this._kernel.CreateFunctionFromMethod(() => { }, "Function1"),
            this._kernel.CreateFunctionFromMethod(() => { }, "Function2"),
        ]);

        Assert.NotNull(plugin);
        Assert.Empty(this._kernel.Plugins);

        Assert.Equal("coolplugin", plugin.Name);
        Assert.Equal("the description", plugin.Description);
        Assert.Equal(2, plugin.FunctionCount);
        Assert.True(plugin.Contains("Function1"));
        Assert.True(plugin.Contains("Function2"));
    }

    [Fact]
    public void ImportPluginFromFunctions()
    {
        this._kernel.ImportPluginFromFunctions("coolplugin",
        [
            this._kernel.CreateFunctionFromMethod(() => { }, "Function1"),
            this._kernel.CreateFunctionFromMethod(() => { }, "Function2"),
        ]);

        Assert.Single(this._kernel.Plugins);

        KernelPlugin plugin = this._kernel.Plugins["coolplugin"];
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
        this._kernel.ImportPluginFromFunctions("coolplugin", "the description",
        [
            this._kernel.CreateFunctionFromMethod(() => { }, "Function1"),
            this._kernel.CreateFunctionFromMethod(() => { }, "Function2"),
        ]);

        Assert.Single(this._kernel.Plugins);

        KernelPlugin plugin = this._kernel.Plugins["coolplugin"];
        Assert.Equal("coolplugin", plugin.Name);
        Assert.Equal("the description", plugin.Description);
        Assert.NotNull(plugin);

        Assert.Equal(2, plugin.FunctionCount);
        Assert.True(plugin.Contains("Function1"));
        Assert.True(plugin.Contains("Function2"));
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldCreatePluginFromType(JsonSerializerOptions? jsos)
    {
        // Arrange & Act
        KernelPlugin plugin = jsos is not null ?
            plugin = this._kernel.CreatePluginFromType<MyPlugin>(jsonSerializerOptions: jsos, pluginName: "p1") :
            plugin = this._kernel.CreatePluginFromType<MyPlugin>(pluginName: "p1");

        // Assert
        await AssertPluginWithSingleFunction(this._kernel, plugin);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldImportPluginFromType(JsonSerializerOptions? jsos)
    {
        // Arrange & Act
        KernelPlugin plugin = jsos is not null ?
            plugin = this._kernel.ImportPluginFromType<MyPlugin>(jsonSerializerOptions: jsos, pluginName: "p1") :
            plugin = this._kernel.ImportPluginFromType<MyPlugin>(pluginName: "p1");

        // Assert
        Assert.Single(this._kernel.Plugins);

        await AssertPluginWithSingleFunction(this._kernel, plugin);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldImportPluginFromObject(JsonSerializerOptions? jsos)
    {
        // Arrange
        var myPlugin = new MyPlugin();

        // Act
        KernelPlugin plugin = jsos is not null ?
            plugin = this._kernel.ImportPluginFromObject(myPlugin, jsonSerializerOptions: jsos, pluginName: "p1") :
            plugin = this._kernel.ImportPluginFromObject(myPlugin, pluginName: "p1");

        // Assert
        Assert.Single(this._kernel.Plugins);

        await AssertPluginWithSingleFunction(this._kernel, plugin);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldCreatePluginFromObject(JsonSerializerOptions? jsos)
    {
        // Arrange
        var myPlugin = new MyPlugin();

        // Arrange & Act
        KernelPlugin plugin = jsos is not null ?
            plugin = this._kernel.CreatePluginFromObject(myPlugin, jsonSerializerOptions: jsos, pluginName: "p1") :
            plugin = this._kernel.CreatePluginFromObject(myPlugin, pluginName: "p1");

        // Assert
        await AssertPluginWithSingleFunction(this._kernel, plugin);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldAddPluginFromTypeToKernelPluginsCollection(JsonSerializerOptions? jsos)
    {
        // Arrange & Act
        KernelPlugin plugin = jsos is not null ?
            plugin = this._kernel.Plugins.AddFromType<MyPlugin>(jsonSerializerOptions: jsos, pluginName: "p1") :
            plugin = this._kernel.Plugins.AddFromType<MyPlugin>(pluginName: "p1");

        // Assert
        Assert.Single(this._kernel.Plugins);

        await AssertPluginWithSingleFunction(this._kernel, plugin);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldAddPluginFromTypeToKernelBuilderPlugins(JsonSerializerOptions? jsos)
    {
        // Arrange
        var kernelBuilder = new KernelBuilder();

        // Act
        if (jsos is not null)
        {
            kernelBuilder.AddFromType<MyPlugin>(jsonSerializerOptions: jsos, pluginName: "p1");
        }
        else
        {
            kernelBuilder.AddFromType<MyPlugin>(pluginName: "p1");
        }

        var kernel = kernelBuilder.Build();

        // Assert
        var plugin = Assert.Single(kernel.Plugins);

        await AssertPluginWithSingleFunction(this._kernel, plugin);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldAddPluginFromObjectToKernelPluginsCollection(JsonSerializerOptions? jsos)
    {
        // Arrange
        var myPlugin = new MyPlugin();

        // Act
        KernelPlugin plugin = jsos is not null ?
            plugin = this._kernel.Plugins.AddFromObject(myPlugin, jsonSerializerOptions: jsos, pluginName: "p1") :
            plugin = this._kernel.Plugins.AddFromObject(myPlugin, pluginName: "p1");

        // Assert
        Assert.Single(this._kernel.Plugins);

        await AssertPluginWithSingleFunction(this._kernel, plugin);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldAddPluginFromObjectToKernelBuilderPlugins(JsonSerializerOptions? jsos)
    {
        // Arrange
        var kernelBuilder = new KernelBuilder();
        var myPlugin = new MyPlugin();

        // Act
        if (jsos is not null)
        {
            kernelBuilder.AddFromObject(myPlugin, jsonSerializerOptions: jsos, pluginName: "p1");
        }
        else
        {
            kernelBuilder.AddFromObject(myPlugin, pluginName: "p1");
        }

        var kernel = kernelBuilder.Build();

        // Assert
        var plugin = Assert.Single(kernel.Plugins);

        await AssertPluginWithSingleFunction(kernel, plugin);
    }

    private static async Task AssertPluginWithSingleFunction(Kernel kernel, KernelPlugin plugin)
    {
        // Assert plugin properties
        Assert.Equal("p1", plugin.Name);
        Assert.Single(plugin);

        // Assert function prperties
        KernelFunction function = plugin["MyMethod"];

        Assert.NotEmpty(function.Metadata.Parameters);
        Assert.NotNull(function.Metadata.Parameters[0].Schema);
        Assert.Equal("{\"type\":\"object\",\"properties\":{\"Value\":{\"type\":[\"string\",\"null\"]}}}", function.Metadata.Parameters[0].Schema!.ToString());

        Assert.NotNull(function.Metadata.ReturnParameter);
        Assert.NotNull(function.Metadata.ReturnParameter.Schema);
        Assert.Equal("{\"type\":\"object\",\"properties\":{\"Result\":{\"type\":\"integer\"}}}", function.Metadata.ReturnParameter.Schema!.ToString());

        // Assert function invocation
        var invokeResult = await function.InvokeAsync(kernel, new() { ["p1"] = """{"Value": "34"}""" }); // Check marshaling logic that deserialize JSON into target type using JSOs
        var result = invokeResult?.GetValue<TestReturnType>();
        Assert.Equal(34, result?.Result);
    }

    private sealed class MyPlugin
    {
        [KernelFunction]
        private TestReturnType MyMethod(TestParameterType p1)
        {
            return new TestReturnType() { Result = int.Parse(p1.Value!) };
        }
    }
}
