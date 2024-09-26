// Copyright (c) Microsoft. All rights reserved.

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
    /// <returns></returns>
    [Fact(Skip = "Need to refactor test to not account for order of steps collection.")]
    public async Task ExecuteAsyncExecutesStepsCorrectlyAsync()
    {
        // Arrange
        var processState = new KernelProcessState { Name = "TestProcess", Id = "123" };
        var mockKernelProcess = new KernelProcess(processState.Id,
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
        Assert.Equal("Step1", localProcess._steps[0].Name);
        Assert.Equal("Step2", localProcess._steps[1].Name);
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
