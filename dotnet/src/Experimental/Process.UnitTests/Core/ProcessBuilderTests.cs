// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Xunit;

namespace Microsoft.SemanticKernel.Process.Core.UnitTests;

/// <summary>
/// Unit tests for the ProcessBuilder class.
/// </summary>
public class ProcessBuilderTests
{
    /// <summary>
    /// Process Events to be used when using <see cref="ProcessBuilder{TEvents}"/>
    /// </summary>
    public enum ProcessTestEvents
    {
        StartEvent,
        MidProcessEvent,
        EndEvent,
    }

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
    /// Tests the initialization of the ProcessBuilder.
    /// </summary>
    [Fact]
    public void ProcessBuilderWithEventsInitialization()
    {
        // Arrange & Act
        var processBuilder = new ProcessBuilder<ProcessTestEvents>(ProcessName);

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
            Assert.Fail("Expected InvalidOperationException");
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
            Assert.Fail("Expected InvalidOperationException");
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
        Assert.EndsWith("Global.OnError", edgeBuilder.EventId);
    }

    /// <summary>
    /// Verify that the <see cref="ProcessBuilder{TEvents}.LinkEventSubscribersFromType{TEventListeners}(IServiceProvider?)"/> fails when linking empty Event Subscriber class
    /// </summary>
    [Fact]
    public void ProcessBuilderWithProcessEventsAndEmptyEventSubscriber()
    {
        // Arrange
        var processBuilder = new ProcessBuilder<ProcessTestEvents>(ProcessName);

        // Act
        try
        {
            processBuilder.LinkEventSubscribersFromType<EmptyTestEventSubscriber>();
            Assert.Fail("Expected InvalidOperationException");
        }
        catch (InvalidOperationException ex)
        {
            // Assert
            Assert.Equal($"The Event Listener type {nameof(EmptyTestEventSubscriber)} has no functions to extract subscribe methods", ex.Message);
        }
    }

    /// <summary>
    /// Verify that the <see cref="ProcessBuilder{TEvents}.LinkEventSubscribersFromType{TEventListeners}(IServiceProvider?)"/> fails when linking Event Subscriber class
    /// without <see cref="KernelProcessEventsSubscriber{TEvents}.ProcessEventSubscriberAttribute"/>
    /// </summary>
    [Fact]
    public void ProcessBuilderWithProcessEventsAndEventSubscriberWithoutAnnotators()
    {
        // Arrange
        var processBuilder = new ProcessBuilder<ProcessTestEvents>(ProcessName);

        // Act
        try
        {
            processBuilder.LinkEventSubscribersFromType<IncompleteTestEventSubscriber>();
            Assert.Fail("Expected InvalidOperationException");
        }
        catch (InvalidOperationException ex)
        {
            // Assert
            Assert.Equal($"The Event Listener type {nameof(IncompleteTestEventSubscriber)} has functions with no ProcessEventSubscriber Annotations", ex.Message);
        }
    }

    /// <summary>
    /// Verify that the <see cref="ProcessBuilder{TEvents}.LinkEventSubscribersFromType{TEventListeners}(IServiceProvider?)"/> fails when linking Event Subscriber class
    /// with process events that are not linked with <see cref="ProcessStepEdgeBuilder.EmitAsProcessEvent(ProcessEdgeBuilder)"/>
    /// </summary>
    [Fact]
    public void ProcessBuilderWithProcessEventsAndMissingEventForEventSubscriber()
    {
        // Arrange
        var processBuilder = new ProcessBuilder<ProcessTestEvents>(ProcessName);
        var repeaterA = processBuilder.AddStepFromType<RepeatTestStep>("repeaterA");
        var repeaterB = processBuilder.AddStepFromType<RepeatTestStep>("repeaterB");
        var repeaterC = processBuilder.AddStepFromType<RepeatTestStep>("repeaterC");

        processBuilder
            .OnInputEvent(ProcessTestEvents.StartEvent)
            .SendEventTo(new ProcessFunctionTargetBuilder(repeaterA));

        repeaterA
            .OnEvent(RepeatTestStep.OutputEvent)
            // intentionally not connecting EmitAsProcessEvent(processBuilder.GetProcessEvent(ProcessTestEvents.MidProcessEvent))
            .SendEventTo(new ProcessFunctionTargetBuilder(repeaterB));

        repeaterB
            .OnEvent(RepeatTestStep.OutputEvent)
            .EmitAsProcessEvent(processBuilder.GetProcessEvent(ProcessTestEvents.EndEvent));

        // Act
        try
        {
            processBuilder.LinkEventSubscribersFromType<CompleteTestEventSubscriber>();
            Assert.Fail("Expected InvalidOperationException");
        }
        catch (InvalidOperationException ex)
        {
            // Assert
            Assert.Equal($"Cannot link method {nameof(CompleteTestEventSubscriber.onMidProcessEventReceived)} to event {Enum.GetName<ProcessTestEvents>(ProcessTestEvents.MidProcessEvent)}, must make use of EmitAsProcessEvent first or remove unused event from event subscriber.", ex.Message);
        }
    }

    /// <summary>
    /// Verify that the <see cref="ProcessBuilder{TEvents}.LinkEventSubscribersFromType{TEventListeners}(IServiceProvider?)"/> fails when linking Event Subscriber class twice
    /// </summary>
    [Fact]
    public void ProcessBuilderWithProcessEventsAndLinkingTwice()
    {
        // Arrange
        var processBuilder = new ProcessBuilder<ProcessTestEvents>(ProcessName);
        var repeaterA = processBuilder.AddStepFromType<RepeatTestStep>("repeaterA");
        var repeaterB = processBuilder.AddStepFromType<RepeatTestStep>("repeaterB");
        var repeaterC = processBuilder.AddStepFromType<RepeatTestStep>("repeaterC");

        processBuilder
            .OnInputEvent(ProcessTestEvents.StartEvent)
            .SendEventTo(new ProcessFunctionTargetBuilder(repeaterA));

        repeaterA
            .OnEvent(RepeatTestStep.OutputEvent)
            .EmitAsProcessEvent(processBuilder.GetProcessEvent(ProcessTestEvents.MidProcessEvent))
            .SendEventTo(new ProcessFunctionTargetBuilder(repeaterB));

        repeaterB
            .OnEvent(RepeatTestStep.OutputEvent)
            .EmitAsProcessEvent(processBuilder.GetProcessEvent(ProcessTestEvents.EndEvent));

        processBuilder.LinkEventSubscribersFromType<CompleteTestEventSubscriber>();

        // Act
        try
        {
            processBuilder.LinkEventSubscribersFromType<CompleteTestEventSubscriber>();
            Assert.Fail("Expected InvalidOperationException");
        }
        catch (InvalidOperationException ex)
        {
            // Assert
            Assert.Equal("Already linked process to another event subscriber class", ex.Message);
        }
    }

    /// <summary>
    /// Verify that the <see cref="ProcessBuilder{TEvents}.LinkEventSubscribersFromType{TEventListeners}(IServiceProvider?)"/> succeeds when linking an event subscriber with matching events
    /// </summary>
    [Fact]
    public void ProcessBuilderWithProcessEventsAndMatchingEventSubscriber()
    {
        // Arrange
        var processBuilder = new ProcessBuilder<ProcessTestEvents>(ProcessName);
        var repeaterA = processBuilder.AddStepFromType<RepeatTestStep>("repeaterA");
        var repeaterB = processBuilder.AddStepFromType<RepeatTestStep>("repeaterB");
        var repeaterC = processBuilder.AddStepFromType<RepeatTestStep>("repeaterC");

        processBuilder
            .OnInputEvent(ProcessTestEvents.StartEvent)
            .SendEventTo(new ProcessFunctionTargetBuilder(repeaterA));

        repeaterA
            .OnEvent(RepeatTestStep.OutputEvent)
            .EmitAsProcessEvent(processBuilder.GetProcessEvent(ProcessTestEvents.MidProcessEvent))
            .SendEventTo(new ProcessFunctionTargetBuilder(repeaterB));

        repeaterB
            .OnEvent(RepeatTestStep.OutputEvent)
            .EmitAsProcessEvent(processBuilder.GetProcessEvent(ProcessTestEvents.EndEvent));

        // Act & Assert
        processBuilder.LinkEventSubscribersFromType<CompleteTestEventSubscriber>();
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
    private sealed class RepeatTestStep : KernelProcessStep
    {
        /// <summary>
        /// The name of the step.
        /// </summary>
        public static string Name => "RepeatTestStep";
        public static string OutputEvent => "OutputEvent";

        /// <summary>
        /// A method that represents a function for testing.
        /// </summary>
        [KernelFunction]
        public async Task TestFunctionAsync(KernelProcessStepContext context, string response)
        {
            await context.EmitEventAsync(OutputEvent, response);
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

    private sealed class EmptyTestEventSubscriber : KernelProcessEventsSubscriber<ProcessTestEvents> { }

    private sealed class IncompleteTestEventSubscriber : KernelProcessEventsSubscriber<ProcessTestEvents>
    {
        public void onMidProcessEventReceived(string result)
        {
        }

        public void onEndEventReceived(string result)
        {
        }
    }

    private sealed class CompleteTestEventSubscriber : KernelProcessEventsSubscriber<ProcessTestEvents>
    {
        public string? onMidEventValue = null;
        public string? onEndEventValue = null;

        [ProcessEventSubscriber(ProcessTestEvents.MidProcessEvent)]
        public void onMidProcessEventReceived(string result)
        {
            this.onMidEventValue = result;
        }

        [ProcessEventSubscriber(ProcessTestEvents.EndEvent)]
        public void onEndEventReceived(string result)
        {
            this.onEndEventValue = result;
        }
    }
}
