// Copyright (c) Microsoft. All rights reserved.

using System;
using Xunit;

namespace Microsoft.SemanticKernel.Process.Core.UnitTests;

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
    /// Tests that ensures when adding steps to builder, step names are not duplicated.<br/>
    /// For state persistence step names must be unique to ensure they can be mapped correctly when restoring from save state.
    /// </summary>
    [Fact]
    public void InvalidOperationExceptionOnAddStepWithSameStepName()
    {
        // Arrange
        var processBuilder = new ProcessBuilder(ProcessName);
        processBuilder.AddStepFromType<TestStep>(StepName);

        // Act
        try
        {
            processBuilder.AddStepFromType<TestStep>(StepName);
        }
        catch (InvalidOperationException ex)
        {
            // Assert
            Assert.Equal($"Step name {StepName} is already used, assign a different name for step", ex.Message);
        }
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
    /// Tests that ensures when adding process steps to builder, step names are not duplicated.<br/>
    /// For state persistence step names must be unique to ensure they can be mapped correctly when restoring from save state.
    /// </summary>
    [Fact]
    public void InvalidOperationExceptionOnAddSubprocessWithSameStepName()
    {
        // Arrange
        var processBuilder = new ProcessBuilder(ProcessName);
        var subProcessBuilder = new ProcessBuilder(StepName);

        processBuilder.AddStepFromType<TestStep>(StepName);
        // Act
        try
        {
            processBuilder.AddStepFromProcess(subProcessBuilder);
        }
        catch (InvalidOperationException ex)
        {
            // Assert
            Assert.Equal($"Step name {StepName} is already used, assign a different name for step", ex.Message);
        }
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
        Assert.Equal(EventId, edgeBuilder.EventData.EventId);
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
        Assert.Equal(ProcessName, kernelProcess.State.StepId);
        Assert.Single(kernelProcess.Steps);
    }

    /// <summary>
    /// Verify that the <see cref="ProcessStepBuilder.OnFunctionResult(string)"/> method returns a <see cref="ProcessStepEdgeBuilder"/>.
    /// </summary>
    [Fact]
    public void OnFunctionErrorCreatesEdgeBuilder()
    {
        // Arrange
        var processBuilder = new ProcessBuilder(ProcessName);
        var errorStep = processBuilder.AddStepFromType<ErrorStep>();
        var edgeBuilder = processBuilder.OnError().SendEventTo(new ProcessFunctionTargetBuilder(errorStep));
        processBuilder.AddStepFromType<TestStep>();

        // Act
        var kernelProcess = processBuilder.Build();

        // Assert
        Assert.NotNull(edgeBuilder);
        Assert.EndsWith("Global.OnError", edgeBuilder.EventData.EventId);
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
    /// A class that represents a step for testing.
    /// </summary>
    private sealed class ErrorStep : KernelProcessStep
    {
        /// <summary>
        /// A method for unhandling failures at the process level.
        /// </summary>
        [KernelFunction]
        public void GlobalErrorHandler(Exception exception)
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
