// Copyright (c) Microsoft. All rights reserved.

<<<<<<< HEAD
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using SemanticKernel.UnitTests.Functions.JsonSerializerContexts;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelPluginFactoryTests
{
    private readonly Kernel _kernel = new();

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldCreatePluginFromType(JsonSerializerOptions? jsos)
    {
        // Arrange & Act
        KernelPlugin plugin = jsos is not null ?
            plugin = KernelPluginFactory.CreateFromType<MyPlugin>(jsonSerializerOptions: jsos, pluginName: "p1") :
            plugin = KernelPluginFactory.CreateFromType<MyPlugin>(pluginName: "p1");

        // Assert
        await AssertPluginWithSingleFunction(this._kernel, plugin);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldCreatePluginFromObject(JsonSerializerOptions? jsos)
    {
        // Arrange
        var myPlugin = new MyPlugin();

        // Act
        KernelPlugin plugin = jsos is not null ?
            plugin = KernelPluginFactory.CreateFromObject(myPlugin, jsonSerializerOptions: jsos, pluginName: "p1") :
            plugin = KernelPluginFactory.CreateFromObject(myPlugin, pluginName: "p1");

        // Assert
        await AssertPluginWithSingleFunction(this._kernel, plugin);
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
=======
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;
public class KernelPluginFactoryTests
{
    [Fact]
    public async Task ItCanCreateFromObjectAsync()
    {
        // Arrange
        var kernel = new Kernel();
        var args = new KernelArguments { { "param1", "value1" } };
        var target = new MyKernelFunctions();

        // Act
        var plugin = KernelPluginFactory.CreateFromObject(target);
        FunctionResult result = await plugin["Function1"].InvokeAsync(kernel, args);

        // Assert
        Assert.NotNull(plugin);
        Assert.Equal(3, plugin.FunctionCount);
        Assert.Equal("Function1: value1", result.Value);
    }

    [Fact]
    public async Task ItCanCreateFromTypeUsingGenericsAsync()
    {
        // Arrange
        var kernel = new Kernel();
        var args = new KernelArguments { { "param1", "value1" } };

        // Act
        var plugin = KernelPluginFactory.CreateFromType<MyKernelFunctions>();
        FunctionResult result = await plugin["Function1"].InvokeAsync(kernel, args);

        // Assert
        Assert.NotNull(plugin);
        Assert.Equal(3, plugin.FunctionCount);
        Assert.Equal("Function1: value1", result.Value);
    }

    [Fact]
    public async Task ItCanCreateFromTypeAsync()
    {
        // Arrange
        var kernel = new Kernel();
        var args = new KernelArguments { { "param1", "value1" } };
        var instanceType = typeof(MyKernelFunctions);

        // Act
        var plugin = KernelPluginFactory.CreateFromType(instanceType);
        FunctionResult result = await plugin["Function1"].InvokeAsync(kernel, args);

        // Assert
        Assert.NotNull(plugin);
        Assert.Equal(3, plugin.FunctionCount);
        Assert.Equal("Function1: value1", result.Value);
    }

    #region private
    private sealed class MyKernelFunctions
    {
        [KernelFunction("Function1")]
        [Description("Description for function 1.")]
        public string Function1([Description("Description for parameter 1")] string param1) => $"Function1: {param1}";

        [KernelFunction("Function2")]
        [Description("Description for function 2.")]
        public string Function2([Description("Description for parameter 1")] string param1) => $"Function2: {param1}";

        [KernelFunction("Function3")]
        [Description("Description for function 3.")]
        public string Function3([Description("Description for parameter 1")] string param1) => $"Function3: {param1}";
    }
    #endregion
>>>>>>> main
}
