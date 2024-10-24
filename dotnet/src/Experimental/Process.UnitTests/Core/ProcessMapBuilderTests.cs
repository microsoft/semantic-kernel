// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading.Tasks;
using Xunit;

namespace Microsoft.SemanticKernel.Process.Core.UnitTests;

/// <summary>
/// Unit tests for <see cref="ProcessMapBuilder"/>.
/// </summary>
public class ProcessMapBuilderTests
{
    /// <summary>
    /// Verify initialization based on <see cref="ProcessStepBuilder"/>.
    /// </summary>
    [Fact]
    public void ProcessMapBuilderFromStep()
    {
        // Arrange
        ProcessStepBuilder<TestStep> step = new($"One{nameof(TestStep)}");

        // Act
        ProcessMapBuilder map = new(step);

        // Assert
        Assert.NotNull(map.Id);
        Assert.NotNull(map.Name);
        Assert.Contains(nameof(TestStep), map.Name);
        Assert.NotNull(map.TargetFunction);
        Assert.Equal(nameof(TestStep.TestFunction), map.TargetFunction.FunctionName);
        Assert.Equal("value", map.TargetFunction.ParameterName);
    }

    /// <summary>
    /// Verify initialization based on <see cref="ProcessBuilder"/>.
    /// </summary>
    [Fact]
    public void ProcessMapBuilderFromProcess()
    {
        // Arrange
        ProcessBuilder process = new("MapOperation");
        ProcessStepBuilder step = process.AddStepFromType<TestStep>($"One{nameof(TestStep)}");
        process.OnInputEvent("ComputeMapValue").SendEventTo(new ProcessFunctionTargetBuilder(step));

        // Act
        ProcessMapBuilder map = new(process, "ComputeMapValue");

        // Assert
        Assert.NotNull(map.Id);
        Assert.NotNull(map.Name);
        Assert.Contains(process.Name, map.Name);
        Assert.NotNull(map.TargetFunction);
        Assert.Equal(nameof(TestStep.TestFunction), map.TargetFunction.FunctionName);
        Assert.Equal("value", map.TargetFunction.ParameterName);
    }

    ///// <summary>
    ///// Tests the AddStepFromType method to ensure it adds a step correctly.
    ///// </summary>
    //[Fact]
    //public void AddStepFromTypeAddsStep()
    //{
    //    // Arrange
    //    var processBuilder = new ProcessBuilder(ProcessName);

    //    // Act
    //    var stepBuilder = processBuilder.AddStepFromType<TestStep>(StepName);

    //    // Assert
    //    Assert.Single(processBuilder.Steps);
    //    Assert.Equal(StepName, stepBuilder.Name);
    //}

    ///// <summary>
    ///// Tests the AddStepFromProcess method to ensure it adds a sub-process correctly.
    ///// </summary>
    //[Fact]
    //public void AddStepFromProcessAddsSubProcess()
    //{
    //    // Arrange
    //    var processBuilder = new ProcessBuilder(ProcessName);
    //    var subProcessBuilder = new ProcessBuilder(SubProcessName);

    //    // Act
    //    var stepBuilder = processBuilder.AddStepFromProcess(subProcessBuilder);

    //    // Assert
    //    Assert.Single(processBuilder.Steps);
    //    Assert.Equal(SubProcessName, stepBuilder.Name);
    //}

    ///// <summary>
    ///// Tests the OnExternalEvent method to ensure it creates an edge builder correctly.
    ///// </summary>
    //[Fact]
    //public void OnExternalEventCreatesEdgeBuilder()
    //{
    //    // Arrange
    //    var processBuilder = new ProcessBuilder(ProcessName);

    //    // Act
    //    var edgeBuilder = processBuilder.OnInputEvent(EventId);

    //    // Assert
    //    Assert.NotNull(edgeBuilder);
    //    Assert.Equal(EventId, edgeBuilder.EventId);
    //}

    ///// <summary>
    ///// Tests the Build method to ensure it creates a KernelProcess correctly.
    ///// </summary>
    //[Fact]
    //public void BuildCreatesKernelProcess()
    //{
    //    // Arrange
    //    var processBuilder = new ProcessBuilder(ProcessName);
    //    processBuilder.AddStepFromType<TestStep>(StepName);

    //    // Act
    //    var kernelProcess = processBuilder.Build();

    //    // Assert
    //    Assert.NotNull(kernelProcess);
    //    Assert.Equal(ProcessName, kernelProcess.State.Name);
    //    Assert.Single(kernelProcess.Steps);
    //}

    private sealed class TestStep : KernelProcessStep<TestState>
    {
        private TestState? _state;

        public override ValueTask ActivateAsync(KernelProcessStepState<TestState> state)
        {
            this._state = state.State;

            return ValueTask.CompletedTask;
        }

        [KernelFunction]
        public void TestFunction(Guid value)
        {
            Assert.NotNull(this._state);
        }
    }

    private sealed class TestState
    {
        public Guid Value { get; set; }
    }
}
