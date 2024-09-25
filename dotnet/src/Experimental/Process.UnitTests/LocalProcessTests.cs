// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Xunit;

namespace Microsoft.SemanticKernel.Process.UnitTests;

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
        var processState = new KernelProcessState { Name = "TestProcess", Id = "123" };
        var mockKernelProcess = new KernelProcess(processState,
        [
            new(typeof(TestStep), new KernelProcessState { Name = "Step1", Id = "1" }, []),
            new(typeof(TestStep), new KernelProcessState { Name = "Step2", Id = "2" }, []),
        ], []);

        var mockKernel = new Kernel();
        using var localProcess = new LocalProcess(mockKernelProcess, mockKernel, loggerFactory: null);

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
        var processState = new KernelProcessState { Name = "TestProcess" };
        var mockKernelProcess = new KernelProcess(processState,
        [
            new(typeof(TestStep), new KernelProcessState { Name = "Step1", Id = "1" }, []),
            new(typeof(TestStep), new KernelProcessState { Name = "Step2", Id = "2" }, []),
        ], []);

        // Act
        using var localProcess = new LocalProcess(mockKernelProcess, mockKernel, loggerFactory: null);

        // Assert
        Assert.NotEmpty(localProcess.Id);
    }

    /// <summary>
    /// Validates that the <see cref="LocalProcess"/> assigns and Id to the process if one is not already set.
    /// </summary>
    [Fact]
    public void ProcessWithAssignedIdIsNotOverwritenId()
    {
        // Arrange
        var mockKernel = new Kernel();
        var processState = new KernelProcessState { Id = "AlreadSet", Name = "TestProcess" };
        var mockKernelProcess = new KernelProcess(processState,
        [
            new(typeof(TestStep), new KernelProcessState { Name = "Step1", Id = "1" }, []),
            new(typeof(TestStep), new KernelProcessState { Name = "Step2", Id = "2" }, []),
        ], []);

        // Act
        using var localProcess = new LocalProcess(mockKernelProcess, mockKernel, loggerFactory: null);

        // Assert
        Assert.NotEmpty(localProcess.Id);
        Assert.Equal("AlreadSet", localProcess.Id);
    }

    /// <summary>
    /// Validates that the <see cref="LocalProcess"/> assigns and Id to the process if one is not already set.
    /// </summary>
    [Fact]
    public void ProcessWithMissingNameThrows()
    {
        // Arrange
        var mockKernel = new Kernel();
        var processState = new KernelProcessState();

        Func<object?> creatProcessTask = (() =>
        {
#pragma warning disable CS8625 // Cannot convert null literal to non-nullable reference type.
            return new KernelProcess(processState,
            [
                new(typeof(TestStep), new KernelProcessState { Name = "Step1", Id = "1" }, []),
                new(typeof(TestStep), new KernelProcessState { Name = "Step2", Id = "2" }, []),
            ], []);
#pragma warning restore CS8625 // Cannot convert null literal to non-nullable reference type.
        });

        Assert.Throws<ArgumentNullException>(creatProcessTask);
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
