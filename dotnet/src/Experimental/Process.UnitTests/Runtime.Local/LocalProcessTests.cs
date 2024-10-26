// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
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
        var processState = new KernelProcessState(name: "TestProcess", id: "123");
        var mockKernelProcess = new KernelProcess(processState,
        [
            new(typeof(TestStep), new KernelProcessState(name: "Step1", id: "1"), []),
            new(typeof(TestStep), new KernelProcessState(name: "Step2", id: "2"), [])
        ], []);

        var mockKernel = new Kernel();
        using var localProcess = new LocalProcess(mockKernelProcess, mockKernel);

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
    public void ProcessWithMissingIdIsAssignedAnId()
    {
        // Arrange
        var mockKernel = new Kernel();
        var processState = new KernelProcessState(name: "TestProcess");
        var mockKernelProcess = new KernelProcess(processState,
        [
            new(typeof(TestStep), new KernelProcessState(name: "Step1", id: "1"), []),
            new(typeof(TestStep), new KernelProcessState(name: "Step2", id: "2"), [])
        ], []);

        // Act
        using var localProcess = new LocalProcess(mockKernelProcess, mockKernel);

        // Assert
        Assert.NotEmpty(localProcess.Id);
    }

    /// <summary>
    /// Validates that the <see cref="LocalProcess"/> assigns and Id to the process if one is not already set.
    /// </summary>
    [Fact]
    public void ProcessWithAssignedIdIsNotOverwrittenId()
    {
        // Arrange
        var mockKernel = new Kernel();
        var processState = new KernelProcessState(name: "TestProcess", id: "AlreadySet");
        var mockKernelProcess = new KernelProcess(processState,
        [
            new(typeof(TestStep), new KernelProcessState(name: "Step1", id: "1"), []),
            new(typeof(TestStep), new KernelProcessState(name: "Step2", id: "2"), [])
        ], []);

        // Act
        using var localProcess = new LocalProcess(mockKernelProcess, mockKernel);

        // Assert
        Assert.NotEmpty(localProcess.Id);
        Assert.Equal("AlreadySet", localProcess.Id);
    }

    /// <summary>
    /// Validates that the <see cref="LocalProcess"/> assigns and Id to the process if one is not already set.
    /// </summary>
    [Fact]
    public async Task ProcessWithSubprocessAndInvalidTargetThrowsAsync()
    {
        // Arrange
        ProcessBuilder process = new(nameof(ProcessWithSubprocessAndInvalidTargetThrowsAsync));

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

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(
            () =>
                processInstance.StartAsync(
                    kernel,
                    new KernelProcessEvent
                    {
                        Id = "Start"
                    }));
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
