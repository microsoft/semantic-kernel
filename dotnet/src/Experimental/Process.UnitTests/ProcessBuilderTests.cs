// Copyright (c) Microsoft. All rights reserved.

using Xunit;

namespace Microsoft.SemanticKernel.Process.UnitTests;

/// <summary>
/// Unit tests for the ProcessBuilder class.
/// </summary>
public class ProcessBuilderTests
{
    private const string ProcessName = "TestProcess";
    private const string StepName = "TestStep";
    private const string EventId = "TestEvent";
    private const string SubProcessName = "SubProcess";

    /// <summary>
    /// Tests the initialization of the ProcessBuilder.
    /// </summary>
    [Fact]
    public void ProcessBuilderInitialization()
    {
        // Arrange & Act
        var processBuilder = new ProcessBuilder(ProcessName);

        // Assert
        Assert.Equal(ProcessName, processBuilder.Name);
        Assert.Empty(processBuilder.Steps);
    }

    /// <summary>
    /// Tests the AddStepFromType method to ensure it adds a step correctly.
    /// </summary>
    [Fact]
    public void AddStepFromTypeAddsStep()
    {
        // Arrange
        var processBuilder = new ProcessBuilder(ProcessName);

        // Act
        var stepBuilder = processBuilder.AddStepFromType<TestStep>(StepName);

        // Assert
        Assert.Single(processBuilder.Steps);
        Assert.Equal(StepName, stepBuilder.Name);
    }

    /// <summary>
    /// Tests the AddStepFromProcess method to ensure it adds a sub-process correctly.
    /// </summary>
    [Fact]
    public void AddStepFromProcessAddsSubProcess()
    {
        // Arrange
        var processBuilder = new ProcessBuilder(ProcessName);
        var subProcessBuilder = new ProcessBuilder(SubProcessName);

        // Act
        var stepBuilder = processBuilder.AddStepFromProcess(subProcessBuilder);

        // Assert
        Assert.Single(processBuilder.Steps);
        Assert.Equal(SubProcessName, stepBuilder.Name);
    }

    /// <summary>
    /// Tests the OnExternalEvent method to ensure it creates an edge builder correctly.
    /// </summary>
    [Fact]
    public void OnExternalEventCreatesEdgeBuilder()
    {
        // Arrange
        var processBuilder = new ProcessBuilder(ProcessName);

        // Act
        var edgeBuilder = processBuilder.OnInputEvent(EventId);

        // Assert
        Assert.NotNull(edgeBuilder);
        Assert.Equal(EventId, edgeBuilder.EventId);
    }

    /// <summary>
    /// Tests the Build method to ensure it creates a KernelProcess correctly.
    /// </summary>
    [Fact]
    public void BuildCreatesKernelProcess()
    {
        // Arrange
        var processBuilder = new ProcessBuilder(ProcessName);
        processBuilder.AddStepFromType<TestStep>(StepName);

        // Act
        var kernelProcess = processBuilder.Build();

        // Assert
        Assert.NotNull(kernelProcess);
        Assert.Equal(ProcessName, kernelProcess.State.Name);
        Assert.Single(kernelProcess.Steps);
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
