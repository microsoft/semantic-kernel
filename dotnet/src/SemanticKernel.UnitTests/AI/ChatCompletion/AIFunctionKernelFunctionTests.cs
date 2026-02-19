// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.UnitTests.AI.ChatCompletion;

public class AIFunctionKernelFunctionTests
{
    [Fact]
    public void ShouldAssignIsRequiredParameterMetadataPropertyCorrectly()
    {
        // Arrange and Act
        AIFunction aiFunction = AIFunctionFactory.Create((string p1, int? p2 = null) => p1,
            new AIFunctionFactoryOptions { JsonSchemaCreateOptions = new AIJsonSchemaCreateOptions { TransformOptions = new() { RequireAllProperties = false } } });

        AIFunctionKernelFunction sut = new(aiFunction);

        // Assert
        KernelParameterMetadata? p1Metadata = sut.Metadata.Parameters.FirstOrDefault(p => p.Name == "p1");
        Assert.True(p1Metadata?.IsRequired);

        KernelParameterMetadata? p2Metadata = sut.Metadata.Parameters.FirstOrDefault(p => p.Name == "p2");
        Assert.False(p2Metadata?.IsRequired);
    }

    [Fact]
    private void AIFunctionKernelFunctionFromAIFunctionShouldHavePluginName()
    {
        AIFunction aiFunc = AIFunctionFactory.Create(() => { }, "f1");
        Assert.Equal("f1", aiFunc.Name);

        KernelFunction kernelFunction = aiFunc.AsKernelFunction();
        Assert.Equal("f1", kernelFunction.Name);
        Assert.Null(kernelFunction.PluginName);

        Kernel kernel = new();
        kernel.Plugins.AddFromFunctions("Tools", [kernelFunction]);

        KernelFunction pluginFunction = kernel.Plugins.ElementAt(0).ElementAt(0);
        Assert.Equal("f1", pluginFunction.Name);
        Assert.Equal("Tools", pluginFunction.PluginName);
    }

    [Fact]
    public void ShouldUseKernelFunctionNameWhenWrappingKernelFunction()
    {
        // Arrange
        var kernelFunction = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");

        // Act
        AIFunctionKernelFunction sut = new(kernelFunction);

        // Assert
        Assert.Equal("TestFunction", sut.Name);
    }

    [Fact]
    public void ShouldUseKernelFunctionPluginAndNameWhenWrappingKernelFunction()
    {
        // Arrange
        var kernelFunction = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction")
            .Clone("TestPlugin"); // Simulate a plugin name

        // Act
        AIFunctionKernelFunction sut = new(kernelFunction);

        // Assert
        Assert.Equal("TestPlugin_TestFunction", sut.Name);
        Assert.Null(sut.PluginName);
    }

    [Fact]
    public void ShouldUseNameOnlyInToStringWhenWrappingKernelFunctionWithPlugin()
    {
        // Arrange
        var kernelFunction = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction")
            .Clone("TestPlugin");

        // Act
        AIFunctionKernelFunction sut = new(kernelFunction);

        // Assert
        Assert.Equal("TestPlugin_TestFunction", sut.ToString());
    }

    [Fact]
    public void ShouldUseAIFunctionNameWhenWrappingNonKernelFunction()
    {
        // Arrange
        var aiFunction = new TestAIFunction("CustomName");

        // Act
        AIFunctionKernelFunction sut = new(aiFunction);

        // Assert
        Assert.Equal("CustomName", sut.Name);
        Assert.Null(sut.PluginName);
    }

    [Fact]
    public void ShouldPreserveDescriptionFromAIFunction()
    {
        // Arrange
        var aiFunction = new TestAIFunction("TestFunction", "This is a test description");

        // Act
        AIFunctionKernelFunction sut = new(aiFunction);

        // Assert
        Assert.Equal("This is a test description", sut.Description);
    }

    [Fact]
    public void ShouldPreserveRootLevelSchemaDefinitionsFromAIFunction()
    {
        // Arrange
        var aiFunction = new TestAIFunctionWithSchema("TestFunction", """
            {
              "type": "object",
              "properties": {
                "node": {
                  "$ref": "#/$defs/Node"
                }
              },
              "$defs": {
                "Node": {
                  "type": "object",
                  "properties": {
                    "name": {
                      "type": "string"
                    }
                  }
                }
              }
            }
            """);

        // Act
        AIFunctionKernelFunction sut = new(aiFunction);
        var schema = sut.JsonSchema;

        // Assert
        Assert.True(schema.TryGetProperty("$defs", out var defs));
        Assert.True(defs.TryGetProperty("Node", out _));
        Assert.Equal("#/$defs/Node", schema.GetProperty("properties").GetProperty("node").GetProperty("$ref").GetString());
    }

    [Fact]
    public async Task ShouldInvokeUnderlyingAIFunctionWhenInvoked()
    {
        // Arrange
        var testAIFunction = new TestAIFunction("TestFunction");
        AIFunctionKernelFunction sut = new(testAIFunction);
        var kernel = new Kernel();
        var arguments = new KernelArguments();

        // Act
        await sut.InvokeAsync(kernel, arguments);

        // Assert
        Assert.True(testAIFunction.WasInvoked);
    }

    [Fact]
    public async Task ShouldInvokeUnderlyingAIFunctionWhenInvokedAsStreaming()
    {
        // Arrange
        var testAIFunction = new TestAIFunction("TestFunction");
        AIFunctionKernelFunction sut = new(testAIFunction);
        var kernel = new Kernel();
        var streamed = new List<string>();

        // Act
        await foreach (var chunk in sut.InvokeStreamingAsync<string>(kernel, []))
        {
            streamed.Add(chunk);
        }

        // Assert
        Assert.True(testAIFunction.WasInvoked);
        Assert.Single(streamed);
        Assert.Equal("Test result", streamed[0]);
    }

    [Fact]
    public void ShouldCloneCorrectlyWithNewPluginName()
    {
        // Arrange
        var aiFunction = new TestAIFunction("TestFunction");
        AIFunctionKernelFunction original = new(aiFunction);

        // Act
        var cloned = original.Clone("NewPlugin");

        // Assert
        Assert.Equal("NewPlugin", cloned.PluginName);
        Assert.Equal("TestFunction", cloned.Name);
        Assert.Equal("NewPlugin.TestFunction", cloned.ToString());
    }

    [Fact]
    public async Task ClonedFunctionShouldInvokeOriginalAIFunction()
    {
        // Arrange
        var testAIFunction = new TestAIFunction("TestFunction");
        AIFunctionKernelFunction original = new(testAIFunction);
        var cloned = original.Clone("NewPlugin");
        var kernel = new Kernel();
        var arguments = new KernelArguments();

        // Act
        await cloned.InvokeAsync(kernel, arguments);

        // Assert
        Assert.True(testAIFunction.WasInvoked);
    }

    [Fact]
    public async Task ShouldUseProvidedKernelWhenInvoking()
    {
        // Arrange
        var kernel1 = new Kernel();
        var kernel2 = new Kernel();

        // Create a function that returns the kernel's hash code
        var function = KernelFunctionFactory.CreateFromMethod(
            (Kernel k) => k.GetHashCode().ToString(),
            "GetKernelHashCode");

        var aiFunction = new AIFunctionKernelFunction(function);

        // Clone with a new plugin name
        var clonedFunction = aiFunction.Clone("NewPlugin");

        // Act
        var result1 = await clonedFunction.InvokeAsync(kernel1, []);
        var result2 = await clonedFunction.InvokeAsync(kernel2, []);

        // Assert - verify that the results are different when using different kernels
        var result1Str = result1.GetValue<object>()?.ToString();
        var result2Str = result2.GetValue<object>()?.ToString();
        Assert.NotNull(result1Str);
        Assert.NotNull(result2Str);
        Assert.NotEqual(result1Str, result2Str);
    }

    [Fact]
    public void ShouldThrowWhenPluginNameIsNullOrWhitespace()
    {
        // Arrange
        var aiFunction = new TestAIFunction("TestFunction");
        AIFunctionKernelFunction original = new(aiFunction);

        // Act & Assert
        Assert.Throws<ArgumentException>(() => original.Clone(string.Empty));
        Assert.Throws<ArgumentException>(() => original.Clone("   "));
    }

    private sealed class TestAIFunction : AIFunction
    {
        public bool WasInvoked { get; private set; }

        public TestAIFunction(string name, string description = "")
        {
            this.Name = name;
            this.Description = description;
        }

        public override string Name { get; }

        public override string Description { get; }

        protected override ValueTask<object?> InvokeCoreAsync(AIFunctionArguments? arguments = null, CancellationToken cancellationToken = default)
        {
            this.WasInvoked = true;
            return ValueTask.FromResult<object?>("Test result");
        }
    }

    private sealed class TestAIFunctionWithSchema : AIFunction
    {
        private readonly JsonElement _schema;

        public TestAIFunctionWithSchema(string name, string jsonSchema)
        {
            this.Name = name;
            this._schema = JsonDocument.Parse(jsonSchema).RootElement.Clone();
        }

        public override string Name { get; }

        public override JsonElement JsonSchema => this._schema;

        protected override ValueTask<object?> InvokeCoreAsync(AIFunctionArguments? arguments = null, CancellationToken cancellationToken = default)
        {
            return ValueTask.FromResult<object?>("Test result");
        }
    }
}
