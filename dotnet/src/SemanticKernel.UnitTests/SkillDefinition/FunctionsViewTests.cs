// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;
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
            .AddFunction(new FunctionView("f1", "s1", "", new List<ParameterView>(), false))
            .AddFunction(new FunctionView("f2", "s1", "", new List<ParameterView>(), false))
            .AddFunction(new FunctionView("f1", "s2", "", new List<ParameterView>(), false));

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
            .AddFunction(new FunctionView("f1", "s1", "", new List<ParameterView>(), true))
            .AddFunction(new FunctionView("f2", "s1", "", new List<ParameterView>(), true))
            .AddFunction(new FunctionView("f1", "s2", "", new List<ParameterView>(), true));

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
            .AddFunction(new FunctionView("f1", "s1", "", new List<ParameterView>(), true))
            .AddFunction(new FunctionView("f1", "s1", "", new List<ParameterView>(), false));

        // Assert
        Assert.Throws<AmbiguousMatchException>(() => target.IsSemantic("s1", "f1"));
        Assert.Throws<AmbiguousMatchException>(() => target.IsNative("s1", "f1"));
    }

    [Fact]
    public void ItReturnsFunctionParams()
    {
        // Arrange
        var params1 = new List<ParameterView>
        {
            new("p1", "param 1", "default 1"),
            new("p2", "param 2", "default 2")
        };
        var params2 = new List<ParameterView>
        {
            new("p3", "param 3", "default 3"),
            new("p4", "param 4", "default 4")
        };
        var target = new FunctionsView()
            .AddFunction(new FunctionView("semFun", "s1", "", params1, true))
            .AddFunction(new FunctionView("natFun", "s1", "", params2, false));

        // Act
        var semFun = target.SemanticFunctions["s1"];
        var natFun = target.NativeFunctions["s1"];

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

    [Fact]
    public void ItCannotAccessByCastSemanticFunctionsDirectly()
    {
        // Arrange
        var target = new FunctionsView();
        target.AddFunction(new FunctionView("semFun", "s1", "", new List<ParameterView>(), true));

        var result = target.SemanticFunctions;

        // Act
        CannotAccessByCastAssert(result);
    }

    [Fact]
    public void ItCannotAccessByCastNativeFunctionsDirectly()
    {
        // Arrange
        var target = new FunctionsView();
        target.AddFunction(new FunctionView("natFun", "s1", "", new List<ParameterView>(), false));
        var result = target.NativeFunctions;

        // Act
        CannotAccessByCastAssert(result);
    }

    private static void CannotAccessByCastAssert(IReadOnlyDictionary<string, IReadOnlyCollection<FunctionView>> result)
    {
        Assert.ThrowsAny<Exception>(() => (ConcurrentDictionary<string, List<FunctionView>>)result);
        Assert.ThrowsAny<Exception>(() => (Dictionary<string, List<FunctionView>>)result);
        Assert.ThrowsAny<Exception>(() => (IDictionary<string, List<FunctionView>>)result);
        Assert.ThrowsAny<Exception>(() => (IReadOnlyDictionary<string, List<FunctionView>>)result);
        Assert.ThrowsAny<Exception>(() => (IReadOnlyDictionary<string, ICollection<FunctionView>>)result);
        Assert.ThrowsAny<Exception>(() => (IReadOnlyDictionary<string, IList<FunctionView>>)result);

        Assert.ThrowsAny<Exception>(() => (List<FunctionView>)result.Values);
        Assert.ThrowsAny<Exception>(() => (IList<FunctionView>)result.Values);
        Assert.ThrowsAny<Exception>(() => (ICollection<FunctionView>)result.Values);
        Assert.ThrowsAny<Exception>(() => (List<FunctionView>)result.GetEnumerator().Current.Value);
        Assert.ThrowsAny<Exception>(() => (IList<FunctionView>)result.GetEnumerator().Current.Value);
        Assert.ThrowsAny<Exception>(() => (ICollection<FunctionView>)result.GetEnumerator().Current.Value);
    }

    [Fact]
    public async Task ItAddSemanticAndNativeFunctionsShouldBeThreadSafe()
    {
        // Arrange
        var target = new FunctionsView();
        var tasks = new List<Task>();

        // Construct 10 semantically identical native and semantic functions
        const int NumOfFunctions = 100;

        var functionsToBeAdded = Enumerable.Range(1, NumOfFunctions)
                                 .Select(i => new FunctionView($"nativeFunction{i}", "skill", "", new List<ParameterView>(), false))
                                 .Concat(
                                 Enumerable.Range(1, NumOfFunctions)
                                 .Select(i => new FunctionView($"semanticFunction{i}", "skill", "", new List<ParameterView>(), true)))
                                 .ToArray();

        // Launch a number of tasks that concurrently Calls the AddFunction of FunctionsView to ensure no conflicts
        for (int i = 0; i < functionsToBeAdded.Length; i++)
        {
            int index = i;
            tasks.Add(Task.Run(() =>
            {
                target.AddFunction(functionsToBeAdded[index]);
            }));
        }

        // Act
        await Task.WhenAll(tasks);

        // Assert
        Assert.Equal(NumOfFunctions, target.SemanticFunctions["skill"].Count);
        Assert.Equal(NumOfFunctions, target.NativeFunctions["skill"].Count); // Since we added NativeFunctions, there should not be any SemanticFunctions
        for (int i = 1; i <= NumOfFunctions; i++)
        {
            Assert.True(target.IsSemantic("skill", $"semanticFunction{i}")); // Check that semantic functions are indeed present in the Dictionary.
            Assert.True(target.IsNative("skill", $"nativeFunction{i}")); // Check that semantic functions are indeed present in the Dictionary.
        }
    }
}
