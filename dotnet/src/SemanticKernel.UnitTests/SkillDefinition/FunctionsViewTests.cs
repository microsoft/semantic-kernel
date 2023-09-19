// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Microsoft.SemanticKernel.SkillDefinition;
using Xunit;

namespace SemanticKernel.UnitTests.SkillDefinition;

public class FunctionsViewTests
{
    [Fact]
    public void ItIsEmptyByDefault()
    {
        // Act
        var target = new FunctionsView();

        // Assert
        Assert.Empty(target.SemanticFunctions);
        Assert.Empty(target.NativeFunctions);
    }

    [Fact]
    public void ItProvidesCorrectNativeFunctionInfo()
    {
        // Arrange
        var target = new FunctionsView()
            .AddFunction(new FunctionView("f1", "s1"))
            .AddFunction(new FunctionView("f2", "s1"))
            .AddFunction(new FunctionView("f1", "s2"));

        // Assert
        Assert.Equal(2, target.NativeFunctions.Count);
        Assert.Equal(2, target.NativeFunctions["s1"].Count);
        Assert.Single(target.NativeFunctions["s2"]);
        Assert.True(target.IsNative("s1", "f1"));
        Assert.True(target.IsNative("s1", "f2"));
        Assert.True(target.IsNative("s2", "f1"));
        Assert.False(target.IsNative("s5", "f5"));
        Assert.False(target.IsSemantic("s1", "f1"));
    }

    [Fact]
    public void ItProvidesCorrectSemanticFunctionInfo()
    {
        // Arrange
        var target = new FunctionsView()
            .AddFunction(new FunctionView("f1", "s1"))
            .AddFunction(new FunctionView("f2", "s1"))
            .AddFunction(new FunctionView("f1", "s2"));

        // Assert
        Assert.Equal(2, target.SemanticFunctions.Count);
        Assert.Equal(2, target.SemanticFunctions["s1"].Count);
        Assert.Single(target.SemanticFunctions["s2"]);
        Assert.True(target.IsSemantic("s1", "f1"));
        Assert.True(target.IsSemantic("s1", "f2"));
        Assert.True(target.IsSemantic("s2", "f1"));
        Assert.False(target.IsSemantic("s5", "f5"));
        Assert.False(target.IsNative("s1", "f1"));
    }

    [Fact]
    public void ItThrowsOnConflict()
    {
        // Arrange
        var target = new FunctionsView()
            .AddFunction(new FunctionView("f1", "s1"))
            .AddFunction(new FunctionView("f1", "s1"));

        // Assert
        Assert.Throws<AmbiguousMatchException>(() => target.IsSemantic("s1", "f1"));
        Assert.Throws<AmbiguousMatchException>(() => target.IsNative("s1", "f1"));
    }

    [Fact]
    public void ItReturnsFunctionParams()
    {
        // Arrange
        var params1 = new ParameterView[]
        {
            new("p1", "param 1", "default 1"),
            new("p2", "param 2", "default 2")
        };
        var params2 = new ParameterView[]
        {
            new("p3", "param 3", "default 3"),
            new("p4", "param 4", "default 4")
        };
        var target = new FunctionsView()
            .AddFunction(new FunctionView("semFun", "s1") { Parameters = params1 })
            .AddFunction(new FunctionView("natFun", "s1") { Parameters = params2 });

        // Act
        List<FunctionView> semFun = target.SemanticFunctions["s1"];
        List<FunctionView> natFun = target.NativeFunctions["s1"];

        // Assert
        Assert.Single(semFun);
        Assert.Single(natFun);
        Assert.Equal("p1", semFun.First().Parameters[0].Name);
        Assert.Equal("p2", semFun.First().Parameters[1].Name);
        Assert.Equal("p3", natFun.First().Parameters[0].Name);
        Assert.Equal("p4", natFun.First().Parameters[1].Name);
        Assert.Equal("param 1", semFun.First().Parameters[0].Description);
        Assert.Equal("param 2", semFun.First().Parameters[1].Description);
        Assert.Equal("param 3", natFun.First().Parameters[0].Description);
        Assert.Equal("param 4", natFun.First().Parameters[1].Description);
        Assert.Equal("default 1", semFun.First().Parameters[0].DefaultValue);
        Assert.Equal("default 2", semFun.First().Parameters[1].DefaultValue);
        Assert.Equal("default 3", natFun.First().Parameters[0].DefaultValue);
        Assert.Equal("default 4", natFun.First().Parameters[1].DefaultValue);
    }
}
