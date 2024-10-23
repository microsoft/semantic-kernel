// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using Microsoft.Extensions.Logging.Abstractions;
using Xunit;

namespace Microsoft.SemanticKernel.Process.Runtime.UnitTests;

/// <summary>
/// Unit tests for the ability to clone:
/// - <see cref="KernelProcessStepState"/>.
/// - <see cref="KernelProcessStepInfo"/>.
/// - <see cref="KernelProcess"/>.
/// </summary>
public class CloneTests
{
    /// <summary>
    /// Verify result of cloning <see cref="KernelProcessStepState"/>.
    /// </summary>
    [Fact]
    public void VerifyCloneStepStateTest()
    {
        // Arrange
        KernelProcessStepState state = new(nameof(VerifyCloneStepStateTest), "test");

        // Act
        KernelProcessStepState copy = state.Clone(typeof(KernelProcessStepState), null);

        // Assert
        Assert.Equal(state, copy);
    }

    /// <summary>
    /// Verify result of cloning <see cref="KernelProcessStepState{TState}"/>.
    /// </summary>
    [Fact]
    public void VerifyCloneTypedStepStateTest()
    {
        // Arrange
        KernelProcessStepState<TestState> state = new(nameof(VerifyCloneTypedStepStateTest), "test") { State = new TestState() };

        // Act
        KernelProcessStepState copy = state.Clone(state.GetType(), typeof(TestState));

        // Assert
        Assert.Equal(state, copy);
    }

    /// <summary>
    /// Verify result of cloning a simple <see cref="KernelProcessStepInfo"/>.
    /// </summary>
    [Fact]
    public void VerifyCloneSimpleStepTest()
    {
        // Arrange
        KernelProcessStepInfo source = new(typeof(KernelProcessStepState), new(nameof(VerifyCloneSimpleStepTest), "test"), []);

        // Act
        KernelProcessStepInfo copy = source.Clone(NullLogger.Instance);

        // Assert
        Assert.Equivalent(source, copy);
    }

    /// <summary>
    /// Verify result of cloning a <see cref="KernelProcessStepInfo"/> with typed state and edges.
    /// </summary>
    [Fact]
    public void VerifyCloneRealStepTest()
    {
        // Arrange
        KernelProcessStepState<TestState> state = new(nameof(VerifyCloneRealStepTest), "test") { State = new TestState() };
        KernelProcessStepInfo source = new(typeof(KernelProcessStepState<TestState>), state, CreateTestEdges());

        // Act
        KernelProcessStepInfo copy = source.Clone(NullLogger.Instance);

        // Assert
        Assert.Equivalent(source, copy);
    }

    /// <summary>
    /// Verify result of cloning a <see cref="KernelProcess"/>.
    /// </summary>
    [Fact]
    public void VerifyCloneSingleProcessTest()
    {
        // Arrange
        KernelProcessStepInfo step = new(typeof(KernelProcessStepState), new(nameof(VerifyCloneSingleProcessTest), "teststep"), []);
        KernelProcessState processState = new(nameof(VerifyCloneSingleProcessTest), "test");
        KernelProcess source = new(processState, [step], CreateTestEdges());

        // Act
        KernelProcess copy = source.CloneProcess(NullLogger.Instance);

        // Assert
        Assert.Equivalent(source, copy);
    }

    /// <summary>
    /// Verify result of cloning a <see cref="KernelProcess"/> with a subprocess.
    /// </summary>
    [Fact]
    public void VerifyCloneNestedProcessTest()
    {
        // Arrange
        KernelProcessStepInfo step = new(typeof(KernelProcessStepState), new(nameof(VerifyCloneNestedProcessTest), "teststep"), []);
        KernelProcess subProcess = new(new(nameof(VerifyCloneNestedProcessTest), "inner"), [step], CreateTestEdges());
        KernelProcess source = new(new(nameof(VerifyCloneNestedProcessTest), "outer"), [subProcess], []);

        // Act
        KernelProcess copy = source.CloneProcess(NullLogger.Instance);

        // Assert
        Assert.Equivalent(source, copy);
    }

    private static Dictionary<string, List<KernelProcessEdge>> CreateTestEdges() =>
        new()
        {
            {
                "sourceId",
                [
                    new KernelProcessEdge("sourceId", new KernelProcessFunctionTarget("sourceId", "targetFunction", "targetParameter", "targetEventId")),
                ]
            }
        };

    private sealed record TestState
    {
        public Guid Value { get; set; }
    };
}
