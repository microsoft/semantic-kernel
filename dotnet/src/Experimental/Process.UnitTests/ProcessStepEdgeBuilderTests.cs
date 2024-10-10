// Copyright (c) Microsoft. All rights reserved.

using System;
using Xunit;

namespace Microsoft.SemanticKernel.Tests;

/// <summary>
/// Unit tests for the <see cref="ProcessStepEdgeBuilder"/> class.
/// </summary>
public class ProcessStepEdgeBuilderTests
{
    /// <summary>
    /// Verify the constructor initializes properties.
    /// </summary>
    [Fact]
    public void ConstructorShouldInitializeProperties()
    {
        // Arrange
        var source = new ProcessStepBuilder<TestStep>(TestStep.Name);
        var eventType = "Event1";

        // Act
        var builder = new ProcessStepEdgeBuilder(source, eventType);

        // Assert
        Assert.Equal(source, builder.Source);
        Assert.Equal(eventType, builder.EventId);
    }

    /// <summary>
    /// Verify that the <see cref="ProcessStepEdgeBuilder.SendEventTo(ProcessFunctionTargetBuilder)"/> method sets the output target.
    /// </summary>
    [Fact]
    public void SendEventToShouldSetOutputTarget()
    {
        // Arrange
        var source = new ProcessStepBuilder<TestStep>(TestStep.Name);
        var eventType = "Event1";
        var builder = new ProcessStepEdgeBuilder(source, eventType);
        var outputTarget = new ProcessFunctionTargetBuilder(source);

        // Act
        builder.SendEventTo(outputTarget);

        // Assert
        Assert.Equal(outputTarget, builder.OutputTarget); // Assuming GetOutputTarget() is a method to access _outputTarget
        Assert.Equal(outputTarget, builder.Target); // Assuming GetOutputTarget() is a method to access _outputTarget
    }

    /// <summary>
    /// Verify that the <see cref="ProcessStepEdgeBuilder.SendEventTo(ProcessFunctionTargetBuilder)"/> method throws if the output target is already set.
    /// </summary>
    [Fact]
    public void SendEventToShouldThrowIfOutputTargetAlreadySet()
    {
        // Arrange
        var source = new ProcessStepBuilder<TestStep>(TestStep.Name);
        var eventType = "Event1";
        var builder = new ProcessStepEdgeBuilder(source, eventType);
        var outputTarget1 = new ProcessFunctionTargetBuilder(source);
        var outputTarget2 = new ProcessFunctionTargetBuilder(source);

        // Act
        builder.SendEventTo(outputTarget1);

        // Assert
        Assert.Throws<InvalidOperationException>(() => builder.SendEventTo(outputTarget2));
    }

    /// <summary>
    /// Verify that the <see cref="ProcessStepEdgeBuilder.StopProcess"/> method sets the output target to the end step.
    /// </summary>
    [Fact]
    public void StopProcessShouldSetOutputTargetToEndStep()
    {
        // Arrange
        var source = new ProcessStepBuilder<TestStep>(TestStep.Name);
        var eventType = "Event1";
        var builder = new ProcessStepEdgeBuilder(source, eventType);

        // Act
        builder.StopProcess();

        // Assert
        Assert.Equal(EndStep.Instance, builder.OutputTarget?.Step);
        Assert.Equal(EndStep.Instance, builder.Target?.Step);
    }

    /// <summary>
    /// Verify that the <see cref="ProcessStepEdgeBuilder.StopProcess"/> method throws if the output target is already set.
    /// </summary>
    [Fact]
    public void StopProcessShouldThrowIfOutputTargetAlreadySet()
    {
        // Arrange
        var source = new ProcessStepBuilder<TestStep>(TestStep.Name);
        var eventType = "Event1";
        var builder = new ProcessStepEdgeBuilder(source, eventType);
        var outputTarget = new ProcessFunctionTargetBuilder(source);

        // Act
        builder.SendEventTo(outputTarget);

        // Assert
        Assert.Throws<InvalidOperationException>(() => builder.StopProcess());
    }

    /// <summary>
    /// Verify that the <see cref="ProcessStepEdgeBuilder.Build"/> method returns a <see cref="KernelProcessEdge"/>.
    /// </summary>
    [Fact]
    public void BuildShouldReturnKernelProcessEdge()
    {
        // Arrange
        var source = new ProcessStepBuilder<TestStep>(TestStep.Name);
        var eventType = "Event1";
        var builder = new ProcessStepEdgeBuilder(source, eventType);
        var outputTarget = new ProcessFunctionTargetBuilder(source);
        builder.SendEventTo(outputTarget);

        // Act
        var edge = builder.Build();

        // Assert
        Assert.NotNull(edge);
        Assert.Equal(source.Id, edge.SourceStepId);
    }

    /// <summary>
    /// A class that represents a step for testing.
    /// </summary>
    private sealed class TestStep : KernelProcessStep<TestState>
    {
        /// <summary>
        /// The name of the step.
        /// </summary>
        public static string Name => "TestStep";

        /// <summary>
        /// A method that represents a function for testing.
        /// </summary>
        [KernelFunction]
        public void TestFunction()
        {
        }
    }

    /// <summary>
    /// A class that represents a state for testing.
    /// </summary>
    private sealed class TestState
    {
    }
}
