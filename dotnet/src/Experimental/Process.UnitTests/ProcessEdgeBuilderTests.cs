// Copyright (c) Microsoft. All rights reserved.

using Xunit;
using Xunit.Sdk;

namespace Microsoft.SemanticKernel.Process.UnitTests;

/// <summary>
/// Unit testing of <see cref="ProcessEdgeBuilder"/>.
/// </summary>
public class ProcessEdgeBuilderTests
{
    /// <summary>
    /// Verify initialization of <see cref="ProcessEdgeBuilder"/>.
    /// </summary>
    [Fact]
    public void ProcessEdgeBuilderInitialization()
    {
        // Arrange
        var processBuilder = new ProcessBuilder("TestProcess");

        // Act
        var edgeBuilder = new ProcessEdgeBuilder(processBuilder, "TestEvent");

        // Assert
        Assert.StrictEqual(processBuilder, edgeBuilder.Source);
        Assert.Equal("TestEvent", edgeBuilder.EventId);
    }

    /// <summary>
    /// Verify initialization of <see cref="ProcessEdgeBuilder"/>.
    /// </summary>
    [Fact]
    public void SendEventToShouldSetOutputTarget()
    {
        // Arrange
        var processBuilder = new ProcessBuilder("TestProcess");
        var source = new ProcessStepBuilder<TestStep>("TestStep");
        var outputTarget = new ProcessFunctionTargetBuilder(source, "TestFunction");

        // Act
        var edgeBuilder = new ProcessEdgeBuilder(processBuilder, "TestEvent");
        edgeBuilder.SendEventTo(outputTarget);

        // Assert
        Assert.Equal(outputTarget, edgeBuilder.Target);
    }

    /// <summary>
    /// Verify initialization of <see cref="ProcessEdgeBuilder"/>.
    /// </summary>
    [Fact]
    public void SendEventToShouldSetMultipleOutputTargets()
    {
        // Arrange
        var processBuilder = new ProcessBuilder("TestProcess");
        var outputTargetA = new ProcessFunctionTargetBuilder(new ProcessStepBuilder<TestStep>("TestStep1"), "TestFunction");
        var outputTargetB = new ProcessFunctionTargetBuilder(new ProcessStepBuilder<TestStep>("TestStep2"), "TestFunction");

        // Act
        var edgeBuilder = new ProcessEdgeBuilder(processBuilder, "TestEvent");
        var edgeBuilder2 = edgeBuilder.SendEventTo(outputTargetA);
        edgeBuilder2.SendEventTo(outputTargetB);

        // Assert
        Assert.Equal(outputTargetA, edgeBuilder.Target);
        Assert.Equal(outputTargetB, edgeBuilder2.Target);
    }

    /// <summary>
    /// A class that represents a step for testing.
    /// </summary>
    private sealed class TestStep : KernelProcessStep
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
    /// Verify behavior of <see cref="ProcessEdgeBuilder.SendEventTo"/>.
    /// </summary>
    [Fact]
    public void SendEventToLinksToTarget()
    {
        // Arrange
        var processBuilder = new ProcessBuilder("TestProcess");
        var edgeBuilder = new ProcessEdgeBuilder(processBuilder, "TestEvent");
        var targetStepBuilder = new ProcessStepEdgeBuilder(processBuilder, "TargetEvent");

        // Act
        edgeBuilder.SendEventTo(targetStepBuilder);

        // Assert
        Assert.Single(processBuilder.Edges);
        Assert.Equal([targetStepBuilder], processBuilder.Edges["TestEvent"]);
    }
}
