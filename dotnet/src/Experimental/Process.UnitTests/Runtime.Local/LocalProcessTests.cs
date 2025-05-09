// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using SemanticKernel.Process.TestsShared.Services;
using SemanticKernel.Process.TestsShared.Setup;
using SemanticKernel.Process.TestsShared.Steps;
using Xunit;

namespace Microsoft.SemanticKernel.Process.Runtime.Local.UnitTests;

/// <summary>
/// Unit tests for the <see cref="LocalProcess"/> class.
/// </summary>
public class LocalProcessTests
{
    /// <summary>
    /// Validates that the <see cref="LocalProcess"/> constructor initializes the steps correctly.
    /// </summary>
    [Fact]
    public async Task ExecuteAsyncInitializesCorrectlyAsync()
    {
        // Arrange
        var processState = new KernelProcessState(name: "TestProcess", version: "v1", id: "123");
        var mockKernelProcess = new KernelProcess(processState,
        [
            new(typeof(TestStep), new KernelProcessState(name: "Step1", version: "v1", id: "1"), []),
            new(typeof(TestStep), new KernelProcessState(name: "Step2", version: "v1", id: "2"), [])
        ], []);

        var mockKernel = new Kernel();
        await using var localProcess = new LocalProcess(mockKernelProcess, mockKernel);
        // Act
        await localProcess.StartAsync();

        // Assert
        Assert.Equal(2, localProcess._steps.Count);
        Assert.Contains(localProcess._steps, s => s.Name == "Step1");
        Assert.Contains(localProcess._steps, s => s.Name == "Step2");
    }

    /// <summary>
    /// Validates that the <see cref="LocalProcess"/> assigns and Id to the process if one is not already set.
    /// </summary>
    [Fact]
    public async Task ProcessWithMissingIdIsAssignedAnIdAsync()
    {
        // Arrange
        var mockKernel = new Kernel();
        var processState = new KernelProcessState(name: "TestProcess", version: "v1");
        var mockKernelProcess = new KernelProcess(processState,
        [
            new(typeof(TestStep), new KernelProcessState(name: "Step1", version: "v1", id: "1"), []),
            new(typeof(TestStep), new KernelProcessState(name: "Step2", version: "v1", id: "2"), [])
        ], []);

        // Act
        await using var localProcess = new LocalProcess(mockKernelProcess, mockKernel);

        // Assert
        Assert.NotEmpty(localProcess.Id);
    }

    /// <summary>
    /// Validates that the <see cref="LocalProcess"/> assigns and Id to the process if one is not already set.
    /// </summary>
    [Fact]
    public async Task ProcessWithAssignedIdIsNotOverwrittenIdAsync()
    {
        // Arrange
        var mockKernel = new Kernel();
        var processState = new KernelProcessState(name: "TestProcess", version: "v1", id: "AlreadySet");
        var mockKernelProcess = new KernelProcess(processState,
        [
            new(typeof(TestStep), new KernelProcessState(name: "Step1", version: "v1", id: "1"), []),
            new(typeof(TestStep), new KernelProcessState(name: "Step2", version: "v1", id: "2"), [])
        ], []);

        // Act
        await using var localProcess = new LocalProcess(mockKernelProcess, mockKernel);

        // Assert
        Assert.NotEmpty(localProcess.Id);
        Assert.Equal("AlreadySet", localProcess.Id);
    }

    /// <summary>
    /// Verify that the function  level error handler is called when a function fails.
    /// </summary>
    [Fact]
    public async Task ProcessFunctionErrorHandledAsync()
    {
        // Arrange
        ProcessBuilder process = new(nameof(ProcessFunctionErrorHandledAsync));

        ProcessStepBuilder testStep = process.AddStepFromType<FailedStep>();
        process.OnInputEvent("Start").SendEventTo(new ProcessFunctionTargetBuilder(testStep));

        ProcessStepBuilder errorStep = process.AddStepFromType<ErrorStep>();
        testStep.OnFunctionError(nameof(FailedStep.TestFailure)).SendEventTo(new ProcessFunctionTargetBuilder(errorStep, nameof(ErrorStep.FunctionErrorHandler)));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        await using LocalKernelProcessContext runningProcess = await processInstance.StartAsync(kernel, new KernelProcessEvent() { Id = "Start" });

        // Assert
        Assert.True(kernel.Data.ContainsKey("error-function"));
        Assert.IsType<KernelProcessError>(kernel.Data["error-function"]);
    }

    /// <summary>
    /// Verify that the process level error handler is called when a function fails.
    /// </summary>
    [Fact]
    public async Task ProcessGlobalErrorHandledAsync()
    {
        // Arrange
        ProcessBuilder process = new(nameof(ProcessFunctionErrorHandledAsync));

        ProcessStepBuilder testStep = process.AddStepFromType<FailedStep>();
        process.OnInputEvent("Start").SendEventTo(new ProcessFunctionTargetBuilder(testStep));

        ProcessStepBuilder errorStep = process.AddStepFromType<ErrorStep>();
        process.OnError().SendEventTo(new ProcessFunctionTargetBuilder(errorStep, nameof(ErrorStep.GlobalErrorHandler)));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        await using LocalKernelProcessContext runningProcess = await processInstance.StartAsync(kernel, new KernelProcessEvent() { Id = "Start" });

        // Assert
        Assert.True(kernel.Data.ContainsKey("error-global"));
        Assert.IsType<KernelProcessError>(kernel.Data["error-global"]);
    }

    /// <summary>
    /// Verify that the function level error handler has precedence over the process level error handler.
    /// </summary>
    [Fact]
    public async Task FunctionErrorHandlerTakesPrecedenceAsync()
    {
        // Arrange
        ProcessBuilder process = new(nameof(ProcessFunctionErrorHandledAsync));

        ProcessStepBuilder testStep = process.AddStepFromType<FailedStep>();
        process.OnInputEvent("Start").SendEventTo(new ProcessFunctionTargetBuilder(testStep));

        ProcessStepBuilder errorStep = process.AddStepFromType<ErrorStep>();
        testStep.OnFunctionError(nameof(FailedStep.TestFailure)).SendEventTo(new ProcessFunctionTargetBuilder(errorStep, nameof(ErrorStep.FunctionErrorHandler)));
        process.OnError().SendEventTo(new ProcessFunctionTargetBuilder(errorStep, nameof(ErrorStep.GlobalErrorHandler)));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        await using LocalKernelProcessContext runningProcess = await processInstance.StartAsync(kernel, new KernelProcessEvent() { Id = "Start" });

        // Assert
        Assert.False(kernel.Data.ContainsKey("error-global"));
        Assert.True(kernel.Data.ContainsKey("error-function"));
        Assert.IsType<KernelProcessError>(kernel.Data["error-function"]);
    }

    [Fact]
    public async Task StartProcessWithKeyedProcessDictSuccessfullyAsync()
    {
        // Arrange
        var processId = "myProcessId";
        var processKey = CommonProcesses.ProcessKeys.CounterProcess;

        var keyedProcesses = CommonProcesses.GetCommonProcessesKeyedDictionary();

        CounterService counterService = new();
        Kernel kernel = KernelSetup.SetupKernelWithCounterService(counterService);

        // Act
        await using LocalKernelProcessContext runningProcess = await LocalKernelProcessFactory.StartAsync(
            kernel, keyedProcesses, processKey, processId, new KernelProcessEvent()
            {
                Id = CommonProcesses.ProcessEvents.StartProcess,
            });

        // Assert
        var processState = await runningProcess.GetStateAsync();
        Assert.NotNull(processState);
        Assert.Equal(processId, processState.State.Id);
        Assert.Equal(processKey, processState.State.Name);
    }

    [Fact]
    public async Task StartProcessWithKeyedProcessDictFailDueMissingKeyAsync()
    {
        // Arrange
        var processId = "myProcessId";
        var processKey = "someKeyThatDoesNotExist";

        var keyedProcesses = CommonProcesses.GetCommonProcessesKeyedDictionary();

        CounterService counterService = new();
        Kernel kernel = KernelSetup.SetupKernelWithCounterService(counterService);

        // Act & Assert
        try
        {
            await using LocalKernelProcessContext runningProcess = await LocalKernelProcessFactory.StartAsync(
                kernel, keyedProcesses, processKey, processId, new KernelProcessEvent()
                {
                    Id = CommonProcesses.ProcessEvents.StartProcess,
                });
        }
        catch (ArgumentException ex)
        {
            // Assert
            Assert.Equal($"The process with key '{processKey}' is not registered.", ex.Message);
        }
    }

    /// <summary>
    /// A class that represents a step for testing.
    /// </summary>
    [Fact]
    public void ProcessWithSubprocessAndInvalidTargetThrows()
    {
        // Arrange
        ProcessBuilder process = new(nameof(ProcessWithSubprocessAndInvalidTargetThrows));

        ProcessBuilder subProcess = new("SubProcess");
        ProcessStepBuilder innerStep = subProcess.AddStepFromType<TestStep>("InnerStep");
        subProcess
            .OnInputEvent("Go")
            .SendEventTo(new ProcessFunctionTargetBuilder(innerStep));
        process
            .OnInputEvent("Start")
            .SendEventTo(subProcess.WhereInputEventIs("Go"));

        ProcessStepBuilder outerStep = process.AddStepFromType<TestStep>("OuterStep");
        innerStep
            .OnEvent(TestStep.EventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(outerStep));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();
    }

    /// <summary>
    /// A class that represents a step for testing.
    /// </summary>
    private sealed class FailedStep : KernelProcessStep
    {
        /// <summary>
        /// A method that represents a function for testing.
        /// </summary>
        [KernelFunction]
        public void TestFailure()
        {
            throw new InvalidOperationException("I failed!");
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
        public void GlobalErrorHandler(KernelProcessError exception, Kernel kernel)
        {
            kernel.Data.Add("error-global", exception);
        }

        /// <summary>
        /// A method for unhandling failures at the function level.
        /// </summary>
        [KernelFunction]
        public void FunctionErrorHandler(KernelProcessError exception, Kernel kernel)
        {
            kernel.Data.Add("error-function", exception);
        }
    }

    /// <summary>
    /// A class that represents a step for testing.
    /// </summary>
    private sealed class TestStep : KernelProcessStep
    {
        public const string EventId = "Next";
        public const string Name = nameof(TestStep);

        [KernelFunction]
        public async Task TestFunctionAsync(KernelProcessStepContext context)
        {
            await context.EmitEventAsync(new() { Id = EventId });
        }
    }
}
