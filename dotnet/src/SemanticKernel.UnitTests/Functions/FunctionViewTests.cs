// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class FunctionViewTests
{
    private readonly Mock<ILoggerFactory> _logger;

    public FunctionViewTests()
    {
        this._logger = new Mock<ILoggerFactory>();
    }

    [Fact]
    public void ItReturnsFunctionParams()
    {
        // Arrange
        var paramsA = new List<ParameterView>
        {
            new("p1", "param 1", "default 1"),
            new("p2", "param 2", "default 2")
        };

        // Act
        var funcViewA = new FunctionView("funcA", "s1", "", paramsA);

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
        var ReturnParameterViewA = new ReturnParameterView("ReturnParameterA", ParameterType: typeof(string), Schema: System.Text.Json.JsonDocument.Parse("\"schema\""));

        // Act
        var funcViewA = new FunctionView("funcA", "s1", "", null, ReturnParameterViewA);

        // Assert
        Assert.NotNull(funcViewA);

        Assert.Equal("ReturnParameterA", funcViewA.ReturnParameter.Description);
        Assert.Equal(typeof(string), funcViewA.ReturnParameter.ParameterType);
        Assert.Equivalent(System.Text.Json.JsonDocument.Parse("\"schema\""), funcViewA.ReturnParameter.Schema);
    }

    [Fact]
    public void ItSupportsValidFunctionName()
    {
        // Act
        var function = SKFunction.FromMethod(Method(ValidFunctionName), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        FunctionView fv = function.Describe();

        // Assert
        Assert.Equal("ValidFunctionName", fv.Name);
    }

    [Fact]
    public void ItSupportsValidFunctionAsyncName()
    {
        // Act
        var function = SKFunction.FromMethod(Method(ValidFunctionNameAsync), loggerFactory: this._logger.Object);
        Assert.NotNull(function);
        FunctionView fv = function.Describe();

        // Assert
        Assert.Equal("ValidFunctionName", fv.Name);
    }

    [Fact]
    public void ItSupportsValidFunctionSKNameAttributeOverride()
    {
        // Arrange
        [SKName("NewTestFunctionName")]
        static void TestFunctionName()
        { }

        // Act
        var function = SKFunction.FromMethod(Method(TestFunctionName), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        FunctionView fv = function.Describe();

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
        var function = SKFunction.FromMethod(Method(TestFunctionName), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        FunctionView fv = function.Describe();

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
        var function = SKFunction.FromMethod(Method(TestFunctionName), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        FunctionView fv = function.Describe();

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
        var function = SKFunction.FromMethod(Method(TestFunctionName), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        FunctionView fv = function.Describe();

        // Assert
        var emptyList = new List<ParameterView>();

        Assert.Equal(emptyList, fv.Parameters);
        Assert.Equal(typeof(void), fv.ReturnParameter.ParameterType);
    }

    private static void ValidFunctionName() { }
    private static async Task ValidFunctionNameAsync()
    {
        var function = SKFunction.FromMethod(Method(ValidFunctionName));
        var context = MockContext("");
        var result = await function.InvokeAsync(new Kernel(new Mock<IAIServiceProvider>().Object), context);
    }

    private static MethodInfo Method(Delegate method)
    {
        return method.Method;
    }

    private static SKContext MockContext(string input)
    {
        var kernel = new Kernel(new Mock<IAIServiceProvider>().Object);
        var serviceProvider = new Mock<IAIServiceProvider>();
        var serviceSelector = new Mock<IAIServiceSelector>();

        return new SKContext(
            kernel,
            serviceProvider.Object,
            serviceSelector.Object,
            new ContextVariables(input)
        );
    }
}
