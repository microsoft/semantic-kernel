// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
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
        Assert.Equal(ProcessName, processBuilder.StepId);
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
        Assert.Equal(StepName, stepBuilder.StepId);
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
        Assert.Equal(SubProcessName, stepBuilder.StepId);
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

    [Fact]
    public void OnEventStepBetweenStepsFailsDueNotSupportedEventWhenStepDoesNotEmitEvent()
    {
        // Arrange
        var testEvent = "Event1";
        var processBuilder = new ProcessBuilder(ProcessName);
        var step1 = processBuilder.AddStepFromType<TestWithStringOutputStep>(StepName);
        var step2 = processBuilder.AddStepFromType<TestWithStringOutputStep>("Step2");

        try
        {
            // Act
            step1.OnEvent(testEvent).SendEventTo(new ProcessFunctionTargetBuilder(step2));
            Assert.Fail("Expected invalid operation exception");
        }
        catch (InvalidOperationException ex)
        {
            // Assert
            Assert.Equal($"Step {StepName} does not emit event {testEvent}. Make sure event name is properly mapped.", ex.Message);
        }
    }

    [Fact]
    public void OnEventStepBetweenStepsFailsDueNotProvidingSpecificFunction()
    {
        // Arrange
        var testEvent = TestWithStringOutputStep.OutputEvents.TestOutputEvent;
        var processBuilder = new ProcessBuilder(ProcessName);
        var step1 = processBuilder.AddStepFromType<TestWithStringOutputStep>("Step1");
        var step2 = processBuilder.AddStepFromType<TestWithStringOutputStep>(StepName);

        try
        {
            // Act
            step1.OnEvent(testEvent).SendEventTo(new ProcessFunctionTargetBuilder(step2));
            Assert.Fail("Expected kernel exception");
        }
        catch (KernelException ex)
        {
            // Assert
            Assert.Equal($"The target step {StepName} has more than one function, so a function name must be provided.", ex.Message);
        }
    }

    [Fact]
    public void OnEventStepBetweenStepsFailsDueInvalidFunctionName()
    {
        // Arrange
        var testEvent = TestWithStringOutputStep.OutputEvents.TestOutputEvent;
        var testFunctionName = "InvalidFunctionName";
        var processBuilder = new ProcessBuilder(ProcessName);
        var step1 = processBuilder.AddStepFromType<TestWithStringOutputStep>("Step1");
        var step2 = processBuilder.AddStepFromType<TestWithStringOutputStep>(StepName);

        try
        {
            // Act
            step1.OnEvent(testEvent).SendEventTo(new ProcessFunctionTargetBuilder(step2, testFunctionName));
            Assert.Fail("Expected kernel exception");
        }
        catch (KernelException ex)
        {
            // Assert
            Assert.Equal($"The function {testFunctionName} does not exist on step {StepName}", ex.Message);
        }
    }

    [Fact]
    public void OnEventFromProcessFailsDueOutputEventMismatch()
    {
        // Arrage
        var testEvent = "SomeEventName";
        var testFunctionName = nameof(TestWithStringOutputStep.TestOneParametersFunction);

        var processBuilder = new ProcessBuilder(ProcessName);
        var innerProcess = processBuilder.AddStepFromProcess(CreateSimpleStringProcess("innerProcess"));
        var step2 = processBuilder.AddStepFromType<TestWithStringOutputStep>(StepName);

        try
        {
            innerProcess.OnEvent(testEvent).SendEventTo(new ProcessFunctionTargetBuilder(step2, testFunctionName));
            Assert.Fail("Expected kernel exception");
        }
        catch (InvalidOperationException ex)
        {
            // Assert
            Assert.Equal($"Output Event {testEvent} is not emitted publicly by {innerProcess.StepId}", ex.Message);
        }
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

    private static ProcessBuilder CreateSimpleStringProcess(string name)
    {
        var processBuilder = new ProcessBuilder(name);
        var step = processBuilder.AddStepFromType<TestWithStringOutputStep>(TestWithStringOutputStep.Name);

        processBuilder
            .OnInputEvent(EventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(step, "TestNoParametersFunction"));

        step.OnEvent(TestWithStringOutputStep.OutputEvents.TestOutputEvent).EmitAsPublicEvent();

        return processBuilder;
    }

    private sealed class TestWithStringOutputStep : KernelProcessStep<TestState>
    {
        /// <summary>
        /// The name of the step.
        /// </summary>
        public static string Name => "TestWithStringOutputStep";

        public static class OutputEvents
        {
            public const string TestOutputEvent = "TestOutputEvent";
        }

        [KernelProcessStepEventMetadata(OutputEvents.TestOutputEvent, typeof(string))]
        [KernelFunction]
        public async Task<string> TestNoParametersFunctionAsync(KernelProcessStepContext context)
        {
            await context.EmitEventAsync(OutputEvents.TestOutputEvent, "Test output");
            return "Test output";
        }

        [KernelFunction]
        public string TestOneParametersFunction(string messageInput)
        {
            return $"Test output: {messageInput}";
        }

        [KernelFunction]
        public List<string> TestListOutput(string messageInput)
        {
            return Enumerable.Repeat(messageInput, 5).ToList();
        }
    }

    private sealed class TestWithIntOutputStep : KernelProcessStep<TestState>
    {
        /// <summary>
        /// The name of the step.
        /// </summary>
        public static string Name => "TestWithStringOutputStep";

        public static class OutputEvents
        {
            public const string TestOutputEvent = "TestOutputEvent";
        }

        [KernelProcessStepEventMetadata(OutputEvents.TestOutputEvent, typeof(int))]
        [KernelFunction]
        public async Task<int> TestNoParametersFunctionAsync(KernelProcessStepContext context)
        {
            await context.EmitEventAsync(OutputEvents.TestOutputEvent, 10000);
            return 10000;
        }

        [KernelFunction]
        public int TestOneParametersFunction(int messageInput)
        {
            return messageInput * 2;
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
