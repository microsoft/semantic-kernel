// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelFunctionMetadataTests
{
    private readonly Mock<ILoggerFactory> _logger;

    public KernelFunctionMetadataTests()
    {
        this._logger = new Mock<ILoggerFactory>();
    }

    [Fact]
    public void ItReturnsFunctionParams()
    {
        // Arrange
        var paramsA = new List<KernelParameterMetadata>
        {
            new("p1") { Description = "param 1", DefaultValue = "default 1" },
            new("p2") { Description = "param 2", DefaultValue = "default 2" },
        };

        // Act
        var funcViewA = new KernelFunctionMetadata("funcA") { Parameters = paramsA };

        // Assert
        Assert.NotNull(funcViewA);

        Assert.Equal("p1", funcViewA.Parameters[0].Name);
        Assert.Equal("p2", funcViewA.Parameters[1].Name);
        Assert.Equal("param 1", funcViewA.Parameters[0].Description);
        Assert.Equal("param 2", funcViewA.Parameters[1].Description);
        Assert.Equal("default 1", funcViewA.Parameters[0].DefaultValue);
        Assert.Equal("default 2", funcViewA.Parameters[1].DefaultValue);
    }

    [Fact]
    public void ItReturnsFunctionReturnParameter()
    {
        // Arrange
        var ReturnParameterViewA = new KernelReturnParameterMetadata
        {
            Description = "ReturnParameterA",
            ParameterType = typeof(string),
            Schema = KernelJsonSchema.Parse("""{"type": "object" }"""),
        };

        // Act
        var funcViewA = new KernelFunctionMetadata("funcA") { ReturnParameter = ReturnParameterViewA };

        // Assert
        Assert.NotNull(funcViewA);

        Assert.Equal("ReturnParameterA", funcViewA.ReturnParameter.Description);
        Assert.Equal(typeof(string), funcViewA.ReturnParameter.ParameterType);
        Assert.Equivalent(KernelJsonSchema.Parse("""{"type": "object" }"""), funcViewA.ReturnParameter.Schema);
    }

    [Fact]
    public void ItSupportsValidFunctionName()
    {
        // Act
        var function = KernelFunctionFactory.CreateFromMethod(ValidFunctionName, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var fv = function.Metadata;

        // Assert
        Assert.Equal("ValidFunctionName", fv.Name);
    }

    [Fact]
    public void ItSupportsValidFunctionAsyncName()
    {
        // Act
        var function = KernelFunctionFactory.CreateFromMethod(ValidFunctionNameAsync, loggerFactory: this._logger.Object);
        Assert.NotNull(function);
        KernelFunctionMetadata fv = function.Metadata;

        // Assert
        Assert.Equal("ValidFunctionName", fv.Name);
    }

    [Fact]
    public void ItSupportsValidFunctionKernelFunctionNameAttributeOverride()
    {
        // Arrange
        [KernelFunction("NewTestFunctionName")]
        static void TestFunctionName()
        { }

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(TestFunctionName, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        KernelFunctionMetadata fv = function.Metadata;

        // Assert
        Assert.Equal("NewTestFunctionName", fv.Name);
    }

    [Fact]
    public void ItSupportsValidAttributeDescriptions()
    {
        // Arrange
        [Description("function description")]
        [return: Description("return parameter description")]
        static void TestFunctionName(
            [Description("first parameter description")] int p1,
            [Description("second parameter description")] int p2)
        { }

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(TestFunctionName, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        KernelFunctionMetadata fv = function.Metadata;

        // Assert
        Assert.Equal("function description", fv.Description);
        Assert.Equal("first parameter description", fv.Parameters[0].Description);
        Assert.Equal(typeof(int), fv.Parameters[0].ParameterType);
        Assert.Equal("second parameter description", fv.Parameters[1].Description);
        Assert.Equal(typeof(int), fv.Parameters[1].ParameterType);
        Assert.Equal("return parameter description", fv.ReturnParameter.Description);
        Assert.Equal(typeof(void), fv.ReturnParameter.ParameterType);
    }

    [Fact]
    public void ItSupportsNoAttributeDescriptions()
    {
        // Arrange
        static void TestFunctionName(int p1, int p2) { }

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(TestFunctionName, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        KernelFunctionMetadata fv = function.Metadata;

        // Assert
        Assert.Equal(string.Empty, fv.Description);
        Assert.Equal(string.Empty, fv.Parameters[0].Description);
        Assert.Equal(typeof(int), fv.Parameters[0].ParameterType);
        Assert.Equal(string.Empty, fv.Parameters[1].Description);
        Assert.Equal(typeof(int), fv.Parameters[1].ParameterType);
        Assert.Equal(string.Empty, fv.ReturnParameter.Description);
        Assert.Equal(typeof(void), fv.ReturnParameter.ParameterType);
    }

    [Fact]
    public void ItSupportsValidNoParameters()
    {
        // Arrange
        static void TestFunctionName() { }

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(TestFunctionName, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        KernelFunctionMetadata fv = function.Metadata;

        // Assert
        var emptyList = new List<KernelParameterMetadata>();

        Assert.Equal(emptyList, fv.Parameters);
        Assert.Equal(typeof(void), fv.ReturnParameter.ParameterType);
    }

    [Fact]
    public void ItSupportsAdditionalUnstructuredMetadata()
    {
        // Arrange
        var additionalMetadataPropertiesA = new ReadOnlyDictionary<string, object?>(new Dictionary<string, object?>
        {
            { "method", "POST" },
            { "path", "/api/v1" },
        });

        // Act
        var actual = new KernelFunctionMetadata("funcA") { AdditionalProperties = additionalMetadataPropertiesA };

        // Assert
        Assert.NotNull(actual);

        Assert.Equal(2, actual.AdditionalProperties.Count);
        Assert.Equal("POST", actual.AdditionalProperties["method"]);
        Assert.Equal("/api/v1", actual.AdditionalProperties["path"]);
    }
    [Fact]
    public void CopyConstructorCopiesPropertiesValues()
    {
        var original = new KernelFunctionMetadata("funcA")
        {
            Description = "description",
            Parameters =
            [
                new("p1") { Description = "param 1", DefaultValue = "default 1" },
                new("p2") { Description = "param 2", DefaultValue = "default 2" },
            ],
            ReturnParameter = new KernelReturnParameterMetadata
            {
                Description = "ReturnParameterA",
                ParameterType = typeof(string),
                Schema = KernelJsonSchema.Parse("""{"type": "object" }"""),
            },
            AdditionalProperties = new ReadOnlyDictionary<string, object?>(new Dictionary<string, object?>
            {
                { "method", "POST" },
                { "path", "/api/v1" },
            }),
            PluginName = "plugin",
            Name = "funcA",
        };

        var copy = new KernelFunctionMetadata(original);
        Assert.Equal(original.AdditionalProperties, copy.AdditionalProperties);
        Assert.Equal(original.Description, copy.Description);
        Assert.Equal(original.Name, copy.Name);
        Assert.Equal(original.Parameters, copy.Parameters);
        Assert.Equal(original.PluginName, copy.PluginName);
        Assert.Equal(original.ReturnParameter, copy.ReturnParameter);
    }

    [Fact]
    public void ItCanBeConstructedWithAllParameters()
    {
        // Test the new constructor that accepts all parameters
        var parameters = new List<KernelParameterMetadata>
        {
            new("param1", "First parameter", "default1", true, typeof(string)),
            new("param2", "Second parameter", 42, false, typeof(int))
        };
        var returnParameter = new KernelReturnParameterMetadata("Return description", typeof(bool));
        var additionalProperties = new ReadOnlyDictionary<string, object?>(new Dictionary<string, object?>
        {
            { "method", "GET" },
            { "endpoint", "/test" }
        });

        var metadata = new KernelFunctionMetadata(
            name: "TestFunction",
            pluginName: "TestPlugin",
            description: "Test function description",
            parameters: parameters,
            returnParameter: returnParameter,
            additionalProperties: additionalProperties);

        Assert.Equal("TestFunction", metadata.Name);
        Assert.Equal("TestPlugin", metadata.PluginName);
        Assert.Equal("Test function description", metadata.Description);
        Assert.Equal(parameters, metadata.Parameters);
        Assert.Equal(returnParameter, metadata.ReturnParameter);
        Assert.Equal(additionalProperties, metadata.AdditionalProperties);
    }

    [Fact]
    public void ItUsesDefaultValuesInNewConstructor()
    {
        // Test that optional parameters have correct default values
        var metadata = new KernelFunctionMetadata("TestFunction");

        Assert.Equal("TestFunction", metadata.Name);
        Assert.Null(metadata.PluginName);
        Assert.Empty(metadata.Description);
        Assert.Empty(metadata.Parameters);
        Assert.NotNull(metadata.ReturnParameter); // Should be default empty instance
        Assert.Empty(metadata.AdditionalProperties);
    }

    [Fact]
    public void ItThrowsForInvalidNameInNewConstructor()
    {
        // Test that the new constructor still validates the name parameter
        Assert.Throws<ArgumentNullException>(() => new KernelFunctionMetadata(null!, "plugin"));
        Assert.Throws<ArgumentException>(() => new KernelFunctionMetadata("", "plugin"));
        Assert.Throws<ArgumentException>(() => new KernelFunctionMetadata("   ", "plugin"));
        Assert.Throws<ArgumentException>(() => new KernelFunctionMetadata("invalid-name!", "plugin"));
    }

    [Fact]
    public void ItHandlesNullDescriptionInNewConstructor()
    {
        // Test that null description is handled correctly
        var metadata = new KernelFunctionMetadata(
            name: "TestFunction",
            pluginName: "TestPlugin",
            description: null);

        Assert.Equal("TestFunction", metadata.Name);
        Assert.Equal("TestPlugin", metadata.PluginName);
        Assert.Empty(metadata.Description); // null description should become empty string
    }

    [Fact]
    public void ItHandlesNullParametersInNewConstructor()
    {
        // Test that null parameters list is handled correctly
        var metadata = new KernelFunctionMetadata(
            name: "TestFunction",
            parameters: null);

        Assert.Equal("TestFunction", metadata.Name);
        Assert.Empty(metadata.Parameters); // null parameters should become empty list
    }

    [Fact]
    public void ItHandlesNullReturnParameterInNewConstructor()
    {
        // Test that null return parameter is handled correctly
        var metadata = new KernelFunctionMetadata(
            name: "TestFunction",
            returnParameter: null);

        Assert.Equal("TestFunction", metadata.Name);
        Assert.NotNull(metadata.ReturnParameter); // Should use default empty instance
        Assert.Empty(metadata.ReturnParameter.Description);
    }

    [Fact]
    public void ItHandlesNullAdditionalPropertiesInNewConstructor()
    {
        // Test that null additional properties is handled correctly
        var metadata = new KernelFunctionMetadata(
            name: "TestFunction",
            additionalProperties: null);

        Assert.Equal("TestFunction", metadata.Name);
        Assert.Empty(metadata.AdditionalProperties); // Should use default empty dictionary
    }

    [Fact]
    public void ItCanBeConstructedWithOnlyNameAndDescription()
    {
        // Test constructor with only name and description
        var metadata = new KernelFunctionMetadata(
            name: "TestFunction",
            description: "Test description");

        Assert.Equal("TestFunction", metadata.Name);
        Assert.Null(metadata.PluginName);
        Assert.Equal("Test description", metadata.Description);
        Assert.Empty(metadata.Parameters);
        Assert.NotNull(metadata.ReturnParameter);
        Assert.Empty(metadata.AdditionalProperties);
    }

    [Fact]
    public void ItCanBeConstructedWithNameAndPluginName()
    {
        // Test constructor with name and plugin name
        var metadata = new KernelFunctionMetadata(
            name: "TestFunction",
            pluginName: "TestPlugin");

        Assert.Equal("TestFunction", metadata.Name);
        Assert.Equal("TestPlugin", metadata.PluginName);
        Assert.Empty(metadata.Description);
        Assert.Empty(metadata.Parameters);
        Assert.NotNull(metadata.ReturnParameter);
        Assert.Empty(metadata.AdditionalProperties);
    }

    [Fact]
    public void ItCanBeConstructedWithEmptyParametersList()
    {
        // Test constructor with explicitly empty parameters list
        var emptyParameters = new List<KernelParameterMetadata>();
        var metadata = new KernelFunctionMetadata(
            name: "TestFunction",
            parameters: emptyParameters);

        Assert.Equal("TestFunction", metadata.Name);
        Assert.Empty(metadata.Parameters);
        Assert.Same(emptyParameters, metadata.Parameters);
    }

    private static void ValidFunctionName() { }
    private static async Task ValidFunctionNameAsync()
    {
        var function = KernelFunctionFactory.CreateFromMethod(ValidFunctionName);
        var result = await function.InvokeAsync(new());
    }
}
