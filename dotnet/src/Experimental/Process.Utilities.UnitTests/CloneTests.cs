// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process.Internal;
using Xunit;

namespace SemanticKernel.Process.Utilities.UnitTests;

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
        KernelProcessStepState state = new(nameof(VerifyCloneStepStateTest), "v1", "test");

        // Act
        KernelProcessStepState copy = state.Clone(typeof(KernelProcessStepState), null, NullLogger.Instance);

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
        KernelProcessStepState<TestState> state = new(nameof(VerifyCloneTypedStepStateTest), "v1", "test") { State = new TestState() };

        // Act
        KernelProcessStepState copy = state.Clone(state.GetType(), typeof(TestState), NullLogger.Instance);

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
        KernelProcessStepInfo source = new(typeof(KernelProcessStep), new(nameof(VerifyCloneSimpleStepTest), "v1", "test"), []);

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
        KernelProcessStepState<TestState> state = new(nameof(VerifyCloneRealStepTest), "v1", "test") { State = new TestState() };
        KernelProcessStepInfo source = new(typeof(KernelProcessStep<TestState>), state, CreateTestEdges());

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
        KernelProcessStepInfo step = new(typeof(KernelProcessStep), new(nameof(VerifyCloneSingleProcessTest), "v1", "teststep"), []);
        KernelProcessState processState = new(nameof(VerifyCloneSingleProcessTest), "v1", "test");
        KernelProcess source = new(processState, [step], CreateTestEdges());

        // Act
        KernelProcess copy = source.CloneProcess(NullLogger.Instance);

        // Assert
        VerifyProcess(source, copy);
    }

    /// <summary>
    /// Verify result of cloning a <see cref="KernelProcess"/> with a subprocess.
    /// </summary>
    [Fact]
    public void VerifyCloneNestedProcessTest()
    {
        // Arrange
        KernelProcessStepInfo step = new(typeof(KernelProcessStep), new(nameof(VerifyCloneNestedProcessTest), "teststep"), []);
        KernelProcess subProcess = new(new(nameof(VerifyCloneNestedProcessTest), "v2", "inner"), [step], CreateTestEdges());
        KernelProcess source = new(new(nameof(VerifyCloneNestedProcessTest), "v1", "outer"), [subProcess], []);

        // Act
        KernelProcess copy = source.CloneProcess(NullLogger.Instance);

        // Assert
        VerifyProcess(source, copy);
    }

    /// <summary>
    /// Verify result of cloning a <see cref="KernelProcess"/> with a <see cref="KernelProcessMap"/>.
    /// </summary>
    [Fact]
    public void VerifyCloneMapStepTest()
    {
        // Arrange
        KernelProcessStepInfo step = new(typeof(KernelProcessStep), new(nameof(VerifyCloneNestedProcessTest), "v1", "teststep"), []);
        KernelProcess mapOperation = new(new(nameof(VerifyCloneNestedProcessTest), "v1", "operation"), [step], CreateTestEdges());
        KernelProcessMap mapStep = new(new(nameof(VerifyCloneNestedProcessTest), "v1", "map"), mapOperation, CreateTestEdges());
        KernelProcess source = new(new(nameof(VerifyCloneNestedProcessTest), "v1", "outer"), [mapStep], []);

        // Act
        KernelProcess copy = source.CloneProcess(NullLogger.Instance);

        // Assert
        VerifyProcess(source, copy);
    }

    /// <summary>
    /// Verify that cloning a <see cref="KernelProcessStepInfo"/> with a new run ID and edges works correctly.
    /// </summary>
    [Fact]
    public void VerifyCloneWithIdAndEdgesTest()
    {
        // Arrange
        string runningId = Guid.NewGuid().ToString();
        string stepName = nameof(VerifyCloneWithIdAndEdgesTest);
        Dictionary<string, List<KernelProcessEdge>> originalStepEdges = new()
        {
            { $"{stepName}.SomeOutputEvent1", CreateTestProcessEdges(1) },
            { $"{stepName}.{stepName}", CreateTestProcessEdges(3) },
        };
        KernelProcessStepInfo step = new(typeof(KernelProcessStep), new(stepName, "v1"), originalStepEdges);

        // Act
        KernelProcessStepInfo copy = step.CloneWithIdAndEdges(runningId, NullLogger.Instance);

        // Assert
        Assert.NotNull(copy);
        Assert.Equal(stepName, copy.State.StepId);
        Assert.Equal(runningId, copy.State.RunId);
        foreach (var (expectedEdges, actualEdges) in step.Edges.Zip(copy.Edges))
        {
            Assert.Contains(runningId, actualEdges.Key);

            var runningIdCountInEvent = actualEdges.Key.Split(runningId).Length - 1;
            Assert.Equal(1, runningIdCountInEvent);

            Assert.Equivalent(expectedEdges.Value, actualEdges.Value);
        }
    }

    private static void VerifyProcess(KernelProcess expected, KernelProcess actual)
    {
        Assert.Equal(expected.State.RunId, actual.State.RunId);
        Assert.Equal(expected.State.StepId, actual.State.StepId);
        Assert.Equal(expected.State.Version, actual.State.Version);
        Assert.Equal(expected.InnerStepType, actual.InnerStepType);
        Assert.Equivalent(expected.Edges, actual.Edges);
        foreach (var (expectedStep, actualStep) in expected.Steps.Zip(actual.Steps))
        {
            if (expectedStep is KernelProcess subProcess)
            {
                Assert.IsType<KernelProcess>(subProcess);
                VerifyProcess(subProcess, (KernelProcess)actualStep);
            }
            else
            {
                Assert.Equivalent(expectedStep, actualStep);
            }
        }
    }

    private static Dictionary<string, List<KernelProcessEdge>> CreateTestEdges() =>
        new()
        {
            {
                "sourceId",
                CreateTestProcessEdges(1)
            }
        };

    private static List<KernelProcessEdge> CreateTestProcessEdges(int count = 1)
    {
        var edges = new List<KernelProcessEdge>();
        for (int i = 0; i < count; i++)
        {
            edges.Add(new KernelProcessEdge($"sourceId{i}", new KernelProcessFunctionTarget($"sourceId{i}", "targetFunction", "targetParameter", $"targetEventId{i}")));
        }
        return edges;
    }

    private sealed record TestState
    {
        public Guid Value { get; set; }
    };
}
