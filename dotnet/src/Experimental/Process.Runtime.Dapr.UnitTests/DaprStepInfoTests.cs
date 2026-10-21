// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.Process.Dapr.Runtime.UnitTests;

/// <summary>
/// Unit tests for the <see cref="DaprStepInfo"/> class.
/// </summary>
public class DaprStepInfoTests
{
    /// <summary>
    /// Tests that ToKernelProcessStepInfo throws when InnerStepDotnetType is not a KernelProcessStep subclass.
    /// </summary>
    [Fact]
    public void ToKernelProcessStepInfoThrowsForInvalidStepType()
    {
        // Arrange
        var stepInfo = new DaprStepInfo
        {
            InnerStepDotnetType = typeof(string).AssemblyQualifiedName!,
            State = new KernelProcessStepState("TestStep", version: "v1"),
            Edges = new Dictionary<string, List<KernelProcessEdge>>()
        };

        // Act & Assert
        var ex = Assert.Throws<KernelException>(() => stepInfo.ToKernelProcessStepInfo());
        Assert.Contains("is not a valid KernelProcessStep type", ex.Message);
    }

    /// <summary>
    /// Tests that ToKernelProcessStepInfo throws when InnerStepDotnetType cannot be resolved.
    /// </summary>
    [Fact]
    public void ToKernelProcessStepInfoThrowsForUnresolvableType()
    {
        // Arrange
        var stepInfo = new DaprStepInfo
        {
            InnerStepDotnetType = "NonExistent.Type, NonExistent.Assembly",
            State = new KernelProcessStepState("TestStep", version: "v1"),
            Edges = new Dictionary<string, List<KernelProcessEdge>>()
        };

        // Act & Assert
        Assert.Throws<KernelException>(() => stepInfo.ToKernelProcessStepInfo());
    }

    /// <summary>
    /// Tests that ToKernelProcessStepInfo succeeds for a valid KernelProcessStep subclass.
    /// </summary>
    [Fact]
    public void ToKernelProcessStepInfoSucceedsForValidStepType()
    {
        // Arrange
        var stepInfo = new DaprStepInfo
        {
            InnerStepDotnetType = typeof(ValidTestStep).AssemblyQualifiedName!,
            State = new KernelProcessStepState("TestStep", version: "v1"),
            Edges = new Dictionary<string, List<KernelProcessEdge>>()
        };

        // Act
        var result = stepInfo.ToKernelProcessStepInfo();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(typeof(ValidTestStep), result.InnerStepType);
    }

    /// <summary>
    /// A valid test step for type validation testing.
    /// </summary>
    public sealed class ValidTestStep : KernelProcessStep
    {
        /// <summary>
        /// A test function.
        /// </summary>
        [KernelFunction]
        public void TestFunction()
        {
        }
    }
}
