// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.AI.FunctionChoiceBehaviors;

public class FunctionChoiceBehaviorDeserializationTests
{
    private readonly Kernel _kernel;

    public FunctionChoiceBehaviorDeserializationTests()
    {
        var plugin = GetTestPlugin();

        this._kernel = new Kernel();
        this._kernel.Plugins.Add(plugin);
    }

    [Fact]
    public void ItShouldDeserializeAutoFunctionChoiceBehaviorFromJsonWithNoFunctionsProperty()
    {
        // Arrange
        var json = """
        {
            "type": "auto"
        }
        """;

        var sut = JsonSerializer.Deserialize<FunctionChoiceBehavior>(json);

        // Act
        var config = sut!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Equal(FunctionChoice.Auto, config.Choice);

        Assert.True(config.AutoInvoke);

        Assert.NotNull(config?.Functions);
        Assert.Equal(3, config.Functions.Count);
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function1");
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function2");
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function3");
    }

    [Fact]
    public void ItShouldDeserializeAutoFunctionChoiceBehaviorFromJsonWithEmptyFunctionsProperty()
    {
        // Arrange
        var json = """
        {
            "type": "auto",
            "functions": []
        }
        """;

        var sut = JsonSerializer.Deserialize<FunctionChoiceBehavior>(json);

        // Act
        var config = sut!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Equal(FunctionChoice.Auto, config.Choice);

        Assert.True(config.AutoInvoke);

        Assert.Null(config?.Functions);
    }

    [Fact]
    public void ItShouldDeserializeAutoFunctionChoiceBehaviorFromJsonWithNotEmptyFunctionsProperty()
    {
        // Arrange
        var json = """
        {
            "type": "auto",
            "functions": ["MyPlugin.Function1", "MyPlugin.Function3"]
        }
        """;

        var sut = JsonSerializer.Deserialize<FunctionChoiceBehavior>(json);

        // Act
        var config = sut!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Equal(FunctionChoice.Auto, config.Choice);

        Assert.True(config.AutoInvoke);

        Assert.NotNull(config?.Functions);
        Assert.Equal(2, config.Functions.Count);
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function1");
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function3");
    }

    [Fact]
    public void ItShouldDeserializeRequiredFunctionChoiceBehaviorFromJsonWithNoFunctionsProperty()
    {
        // Arrange
        var json = """
        {
            "type": "required"
        }
        """;

        var sut = JsonSerializer.Deserialize<FunctionChoiceBehavior>(json);

        // Act
        var config = sut!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Equal(FunctionChoice.Required, config.Choice);

        Assert.True(config.AutoInvoke);

        Assert.NotNull(config?.Functions);
        Assert.Equal(3, config.Functions.Count);
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function1");
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function2");
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function3");
    }

    [Fact]
    public void ItShouldDeserializeRequiredFunctionChoiceBehaviorFromJsonWithEmptyFunctionsProperty()
    {
        // Arrange
        var json = """
        {
            "type": "required",
            "functions": []
        }
        """;

        var sut = JsonSerializer.Deserialize<FunctionChoiceBehavior>(json);

        // Act
        var config = sut!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Equal(FunctionChoice.Required, config.Choice);

        Assert.True(config.AutoInvoke);

        Assert.Null(config?.Functions);
    }

    [Fact]
    public void ItShouldDeserializeRequiredFunctionChoiceBehaviorFromJsonWithNotEmptyFunctionsProperty()
    {
        // Arrange
        var json = """
        {
            "type": "required",
            "functions": ["MyPlugin.Function1", "MyPlugin.Function3"]
        }
        """;

        var sut = JsonSerializer.Deserialize<FunctionChoiceBehavior>(json);

        // Act
        var config = sut!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Equal(FunctionChoice.Required, config.Choice);

        Assert.True(config.AutoInvoke);

        Assert.NotNull(config?.Functions);
        Assert.Equal(2, config.Functions.Count);
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function1");
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function3");
    }

    [Fact]
    public void ItShouldDeserializedNoneFunctionChoiceBehaviorFromJsonWithNoFunctionsProperty()
    {
        // Arrange
        var json = """
        {
            "type": "none"
        }
        """;

        var sut = JsonSerializer.Deserialize<FunctionChoiceBehavior>(json);

        // Act
        var config = sut!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Equal(FunctionChoice.None, config.Choice);

        Assert.False(config.AutoInvoke);

        Assert.NotNull(config?.Functions);
        Assert.Equal(3, config.Functions.Count);
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function1");
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function2");
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function3");
    }

    [Fact]
    public void ItShouldDeserializedNoneFunctionChoiceBehaviorFromJsonWithEmptyFunctionsProperty()
    {
        // Arrange
        var json = """
        {
            "type": "none",
            "functions": []
        }
        """;

        var sut = JsonSerializer.Deserialize<FunctionChoiceBehavior>(json);

        // Act
        var config = sut!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Equal(FunctionChoice.None, config.Choice);

        Assert.False(config.AutoInvoke);

        Assert.Null(config?.Functions);
    }

    [Fact]
    public void ItShouldDeserializedNoneFunctionChoiceBehaviorFromJsonWithNotEmptyFunctionsProperty()
    {
        // Arrange
        var json = """
        {
            "type": "none",
            "functions": ["MyPlugin.Function1", "MyPlugin.Function3"]
        }
        """;

        var sut = JsonSerializer.Deserialize<FunctionChoiceBehavior>(json);

        // Act
        var config = sut!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Equal(FunctionChoice.None, config.Choice);

        Assert.False(config.AutoInvoke);

        Assert.NotNull(config?.Functions);
        Assert.Equal(2, config.Functions.Count);
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function1");
        Assert.Contains(config.Functions, f => f.PluginName == "MyPlugin" && f.Name == "Function3");
    }

    [Fact]
    public void ItShouldDeserializeAutoFunctionChoiceBehaviorFromJsonWithOptions()
    {
        // Arrange
        var json = """
        {
            "type": "auto",
            "options": {
                "allow_parallel_calls": true,
                "allow_concurrent_invocation": true,
                "allow_strict_schema_adherence": true
            }
        }
        """;

        var sut = JsonSerializer.Deserialize<FunctionChoiceBehavior>(json);

        // Act
        var config = sut!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.True(config.Options.AllowParallelCalls);
        Assert.True(config.Options.AllowConcurrentInvocation);
        Assert.True(config.Options.AllowStrictSchemaAdherence);
    }

    [Fact]
    public void ItShouldDeserializeRequiredFunctionChoiceBehaviorFromJsonWithOptions()
    {
        // Arrange
        var json = """
        {
            "type": "required",
            "options": {
                "allow_parallel_calls": true,
                "allow_concurrent_invocation": true,
                "allow_strict_schema_adherence": true
            }
        }
        """;

        var sut = JsonSerializer.Deserialize<FunctionChoiceBehavior>(json);

        // Act
        var config = sut!.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.True(config.Options.AllowParallelCalls);
        Assert.True(config.Options.AllowConcurrentInvocation);
        Assert.True(config.Options.AllowStrictSchemaAdherence);
    }

    private static KernelPlugin GetTestPlugin()
    {
        var function1 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function2");
        var function3 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function3");

        return KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2, function3]);
    }
}
