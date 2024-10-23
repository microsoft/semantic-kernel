// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Xunit;

namespace Microsoft.SemanticKernel.Process.UnitTests;

/// <summary>
/// Unit tests for the <see cref="ProcessStepBuilder"/> class.
/// </summary>
public class ProcessStepBuilderTests
{
    /// <summary>
    /// Verify the constructor initializes properties.
    /// </summary>
    [Fact]
    public void ConstructorShouldInitializeProperties()
    {
        // Arrange
        var name = "TestStep";

        // Act
        var stepBuilder = new TestProcessStepBuilder(name);

        // Assert
        Assert.Equal(name, stepBuilder.Name);
        Assert.NotNull(stepBuilder.Id);
        Assert.NotNull(stepBuilder.FunctionsDict);
        Assert.NotNull(stepBuilder.Edges);
    }

    /// <summary>
    /// Verify that the <see cref="ProcessStepBuilder.OnEvent(string)"/> method returns a <see cref="ProcessStepEdgeBuilder"/>.
    /// </summary>
    [Fact]
    public void OnEventShouldReturnProcessStepEdgeBuilder()
    {
        // Arrange
        var stepBuilder = new TestProcessStepBuilder("TestStep");

        // Act
        var edgeBuilder = stepBuilder.OnEvent("TestEvent");

        // Assert
        Assert.NotNull(edgeBuilder);
        Assert.IsType<ProcessStepEdgeBuilder>(edgeBuilder);
        Assert.EndsWith("TestEvent", edgeBuilder.EventId);
    }

    /// <summary>
    /// Verify that the <see cref="ProcessStepBuilder.OnFunctionResult(string)"/> method returns a <see cref="ProcessStepEdgeBuilder"/>.
    /// </summary>
    [Fact]
    public void OnFunctionResultShouldReturnProcessStepEdgeBuilder()
    {
        // Arrange
        var stepBuilder = new TestProcessStepBuilder("TestStep");

        // Act
        var edgeBuilder = stepBuilder.OnFunctionResult("TestFunction");

        // Assert
        Assert.NotNull(edgeBuilder);
        Assert.IsType<ProcessStepEdgeBuilder>(edgeBuilder);
        Assert.EndsWith("TestFunction.OnResult", edgeBuilder.EventId);
    }

    /// <summary>
    /// Verify that the <see cref="ProcessStepBuilder.OnFunctionResult(string)"/> method returns a <see cref="ProcessStepEdgeBuilder"/>.
    /// </summary>
    [Fact]
    public void OnFunctionErrorShouldReturnProcessStepEdgeBuilder()
    {
        // Arrange
        var stepBuilder = new TestProcessStepBuilder("TestStep");

        // Act
        var edgeBuilder = stepBuilder.OnFunctionError("TestFunction");

        // Assert
        Assert.NotNull(edgeBuilder);
        Assert.IsType<ProcessStepEdgeBuilder>(edgeBuilder);
        Assert.EndsWith("TestFunction.OnError", edgeBuilder.EventId);
    }

    /// <summary>
    /// Verify that the <see cref="ProcessStepBuilder.LinkTo(string, ProcessStepEdgeBuilder)"/> method adds an edge.
    /// </summary>
    [Fact]
    public void LinkToShouldAddEdge()
    {
        // Arrange
        var stepBuilder = new TestProcessStepBuilder("TestStep");
        var edgeBuilder = new ProcessStepEdgeBuilder(stepBuilder, "TestEvent");

        // Act
        stepBuilder.LinkTo("TestEvent", edgeBuilder);

        // Assert
        Assert.True(stepBuilder.Edges.ContainsKey("TestEvent"));
        Assert.Contains(edgeBuilder, stepBuilder.Edges["TestEvent"]);
    }

    /// <summary>
    /// Verify that the <see cref="ProcessStepBuilder.ResolveFunctionTarget(string, string)"/> method throws an exception when no functions exist.
    /// </summary>
    [Fact]
    public void ResolveFunctionTargetShouldThrowExceptionWhenNoFunctionsExist()
    {
        // Arrange
        var stepBuilder = new TestProcessStepBuilder("TestStep");

        // Act & Assert
        Assert.Throws<KernelException>(() => stepBuilder.ResolveFunctionTarget(null, null));
    }

    /// <summary>
    /// Verify that the <see cref="ProcessStepBuilder.ResolveFunctionTarget(string, string)"/> method correctly resolves a function target.
    /// In this case, the function name is provided and the parameter name is not. The target function has no parameters.
    /// </summary>
    [Fact]
    public void ResolveFunctionTargetWithoutParameterShouldReturnFunctionTargetWhenNoneExist()
    {
        // Arrange
        var stepBuilder = new TestProcessStepBuilder("TestStep");
        stepBuilder.FunctionsDict["TestFunction"] = new KernelFunctionMetadata(name: "TestFunction")
        {
            Description = "Test function description",
            Parameters = new List<KernelParameterMetadata>()
        };

        // Act
        var target = stepBuilder.ResolveFunctionTarget("TestFunction", null);

        // Assert
        Assert.NotNull(target);
        Assert.Equal("TestFunction", target.FunctionName);
    }

    /// <summary>
    /// Verify that the <see cref="ProcessStepBuilder.ResolveFunctionTarget(string, string)"/> method correctly resolves a function target.
    /// In this case, the function name is provided and the parameter name is not. The target function has one parameters.
    /// </summary>
    [Fact]
    public void ResolveFunctionTargetWithoutParameterShouldReturnFunctionTargetWhenOnlyOneParameterExists()
    {
        // Arrange
        var stepBuilder = new TestProcessStepBuilder("TestStep");
        stepBuilder.FunctionsDict["TestFunction"] = new KernelFunctionMetadata(name: "TestFunction")
        {
            Description = "Test function description",
            Parameters = [new KernelParameterMetadata("param1")]
        };

        // Act
        var target = stepBuilder.ResolveFunctionTarget("TestFunction", null);

        // Assert
        Assert.NotNull(target);
        Assert.Equal("TestFunction", target.FunctionName);
        Assert.Equal("param1", target.ParameterName);
    }

    /// <summary>
    /// Verify that the <see cref="ProcessStepBuilder.ResolveFunctionTarget(string, string)"/> method throws when it cannot resolve.
    /// In this case, the function name is provided and the parameter name is not. The target function has more than one parameters.
    /// </summary>
    [Fact]
    public void ResolveFunctionTargetWithoutParameterShouldThrowWhenCannotResolveParameter()
    {
        // Arrange
        var stepBuilder = new TestProcessStepBuilder("TestStep");
        stepBuilder.FunctionsDict["TestFunction"] = new KernelFunctionMetadata(name: "TestFunction")
        {
            Description = "Test function description",
            Parameters = [new KernelParameterMetadata("param1"), new KernelParameterMetadata("param2")]
        };

        // Act & Assert
        Assert.Throws<KernelException>(() => stepBuilder.ResolveFunctionTarget("TestFunction", null));
    }

    /// <summary>
    /// Verify that the <see cref="ProcessStepBuilder.ResolveFunctionTarget(string, string)"/> method correctly resolves a function target.
    /// In this case, the function name is not provided, nor is the parameter name. The target function has one function with one parameter.
    /// </summary>
    [Fact]
    public void ResolveFunctionTargetWithoutParameterShouldReturnFunctionTargetWhenOnlyOneFunctionExists()
    {
        // Arrange
        var stepBuilder = new TestProcessStepBuilder("TestStep");
        stepBuilder.FunctionsDict["TestFunction"] = new KernelFunctionMetadata(name: "TestFunction")
        {
            Description = "Test function description",
            Parameters = [new KernelParameterMetadata("param1")]
        };

        // Act
        var target = stepBuilder.ResolveFunctionTarget(null, null);

        // Assert
        Assert.NotNull(target);
        Assert.Equal("TestFunction", target.FunctionName);
        Assert.Equal("param1", target.ParameterName);
    }

    /// <summary>
    /// Verify that the <see cref="ProcessStepBuilder.ResolveFunctionTarget(string, string)"/> method throws when it cannot resolve.
    /// In this case, the function name is provided as is the parameter name. The target has more than one function.
    /// </summary>
    [Fact]
    public void ResolveFunctionTargetWithoutParameterShouldThrowWhenCannotResolveFunction()
    {
        // Arrange
        var stepBuilder = new TestProcessStepBuilder("TestStep");
        stepBuilder.FunctionsDict["TestFunction1"] = new KernelFunctionMetadata(name: "TestFunction1")
        {
            Description = "Test function description",
            Parameters = [new KernelParameterMetadata("param1")]
        };
        stepBuilder.FunctionsDict["TestFunction2"] = new KernelFunctionMetadata(name: "TestFunction2")
        {
            Description = "Test function description",
            Parameters = [new KernelParameterMetadata("param1")]
        };

        // Act & Assert
        Assert.Throws<KernelException>(() => stepBuilder.ResolveFunctionTarget(null, null));
    }

    /// <summary>
    /// A test implementation of <see cref="ProcessStepBuilder"/> for testing purposes.
    /// </summary>
    private sealed class TestProcessStepBuilder : ProcessStepBuilder
    {
        public TestProcessStepBuilder(string name) : base(name) { }

        internal override KernelProcessStepInfo BuildStep()
        {
            return new KernelProcessStepInfo(typeof(TestProcessStepBuilder), new KernelProcessStepState(this.Name, this.Id), []);
        }

        internal override Dictionary<string, KernelFunctionMetadata> GetFunctionMetadataMap()
        {
            return new Dictionary<string, KernelFunctionMetadata>();
        }
    }
}
