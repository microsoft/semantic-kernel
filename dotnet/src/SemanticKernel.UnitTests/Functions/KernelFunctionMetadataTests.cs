// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
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
            Schema = KernelJsonSchema.Parse("\"schema\""),
        };

        // Act
        var funcViewA = new KernelFunctionMetadata("funcA") { ReturnParameter = ReturnParameterViewA };

        // Assert
        Assert.NotNull(funcViewA);

        Assert.Equal("ReturnParameterA", funcViewA.ReturnParameter.Description);
        Assert.Equal(typeof(string), funcViewA.ReturnParameter.ParameterType);
        Assert.Equivalent(KernelJsonSchema.Parse("\"schema\""), funcViewA.ReturnParameter.Schema);
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
    public void ItSupportsValidFunctionSKNameAttributeOverride()
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

    private static void ValidFunctionName() { }
    private static async Task ValidFunctionNameAsync()
    {
        var function = KernelFunctionFactory.CreateFromMethod(ValidFunctionName);
        var result = await function.InvokeAsync(new());
    }
}
