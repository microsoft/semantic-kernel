// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Orchestration;
using Xunit;

namespace SemanticKernel.UnitTests.Orchestration;

/// <summary>
/// Unit tests for <see cref="KernelResult"/> class.
/// </summary>
public class KernelResultTests
{
    private readonly SKContext _context;

    public KernelResultTests()
    {
        this._context = new SKContext();
    }

    [Fact]
    public void ItReturnsCorrectValuesFromFunctionResults()
    {
        // Arrange
        var functionResults = new List<FunctionResult>
        {
            new("function1", this._context, "value1"),
            new("function2", this._context, "value2"),
        };

        // Act
        var kernelResult = KernelResult.FromFunctionResults("value2", functionResults);
        var actualFunctionResults = kernelResult.FunctionResults.ToList();

        // Assert
        Assert.Equal("value2", kernelResult.GetValue<string>());
        Assert.Equal(functionResults.Count, actualFunctionResults.Count);

        for (var i = 0; i < functionResults.Count; i++)
        {
            this.AssertFunctionResult(functionResults[i], actualFunctionResults[i]);
        }
    }

    [Fact]
    public void ToStringWorksCorrectly()
    {
        // Arrange
        var kernelResult = KernelResult.FromFunctionResults("value", Array.Empty<FunctionResult>());

        // Act and Assert
        Assert.Equal("value", kernelResult.ToString());
    }

    private void AssertFunctionResult(FunctionResult expected, FunctionResult actual)
    {
        Assert.Equal(expected.FunctionName, actual.FunctionName);
        Assert.Equal(expected.Context, actual.Context);
        Assert.Equal(expected.Value, actual.Value);
    }
}
