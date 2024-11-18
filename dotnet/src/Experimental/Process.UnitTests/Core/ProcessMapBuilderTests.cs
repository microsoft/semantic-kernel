﻿// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Linq;
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
        ProcessStepBuilder<SimpleTestStep> step = new($"One{nameof(SimpleTestStep)}");

        // Act
        ProcessMapBuilder map = new(step);

        // Assert
        Assert.NotNull(map.Id);
        Assert.NotNull(map.Name);
        Assert.Contains(nameof(SimpleTestStep), map.Name);
        Assert.NotNull(map.MapOperation);
        Assert.Equal(step, map.MapOperation);
    }

    /// <summary>
    /// Verify cannot be a function target.
    /// </summary>
    [Fact]
    public void ProcessMapBuilderFromMap()
    {
        // Arrange
        ProcessStepBuilder<SimpleTestStep> step = new($"One{nameof(SimpleTestStep)}");
        ProcessMapBuilder map1 = new(step);
        ProcessMapBuilder map2 = new(step);

        // Act & Assert
        Assert.Throws<ArgumentException>(() => map1.OnEvent("any").SendEventTo(new ProcessFunctionTargetBuilder(map2)));
    }

    /// <summary>
    /// Verify initialization based on <see cref="ProcessBuilder"/>.
    /// </summary>
    [Fact]
    public void ProcessMapBuilderFromProcess()
    {
        // Arrange
        ProcessBuilder process = new("MapOperation");
        ProcessStepBuilder step = process.AddStepFromType<SimpleTestStep>($"One{nameof(SimpleTestStep)}");
        process.OnInputEvent("ComputeMapValue").SendEventTo(new ProcessFunctionTargetBuilder(step));

        // Act
        ProcessMapBuilder map = new(process);

        // Assert
        Assert.NotNull(map.Id);
        Assert.NotNull(map.Name);
        Assert.Contains(process.Name, map.Name);
        Assert.NotNull(map.MapOperation);
        Assert.Equal(process, map.MapOperation);
    }

    /// <summary>
    /// Verify <see cref="ProcessMapBuilder"/> is able to define targets / output edges.
    /// </summary>
    [Fact]
    public void ProcessMapBuilderCanDefineTarget()
    {
        // Arrange
        ProcessStepBuilder<SimpleTestStep> step = new($"One{nameof(SimpleTestStep)}");
        ProcessMapBuilder map = new(step);

        // Act
        ProcessStepBuilder<SimpleTestStep> step2 = new($"Two{nameof(SimpleTestStep)}");
        map.OnEvent("Any").SendEventTo(new ProcessFunctionTargetBuilder(step2));

        // Assert
        Assert.Single(map.Edges);
        Assert.Single(map.Edges.Single().Value);
        Assert.NotNull(map.Edges.Single().Value[0].Target);
        Assert.Equal(step2, map.Edges.Single().Value[0].Target!.Step);

        // Act
        KernelProcessStepInfo processMap = map.BuildStep();

        // Assert
        Assert.NotNull(processMap);
        Assert.Equal(processMap.Edges.Count, map.Edges.Count);
        Assert.Equal(processMap.Edges.Single().Value.Count, map.Edges.First().Value.Count);
        Assert.Equal(processMap.Edges.Single().Value.Single().OutputTarget!.StepId, map.Edges.Single().Value[0].Target!.Step.Id);
    }

    /// <summary>
    /// Verify <see cref="ProcessMapBuilder.GetFunctionMetadataMap"/> always throws.
    /// </summary>
    [Fact]
    public void ProcessMapBuilderGetFunctionMetadataMapThrows()
    {
        // Arrange
        ProcessStepBuilder<SimpleTestStep> step = new($"One{nameof(SimpleTestStep)}");
        ProcessMapBuilder map = new(step);

        // Act
        Assert.Throws<NotImplementedException>(() => map.GetFunctionMetadataMap());
    }

    /// <summary>
    /// Verify <see cref="ProcessMapBuilder.BuildStep"/> produces the
    /// expected <see cref="KernelProcessMap"/>.
    /// </summary>
    [Fact]
    public void ProcessMapBuilderWillBuild()
    {
        // Arrange
        ProcessStepBuilder<SimpleTestStep> step = new($"One{nameof(SimpleTestStep)}");
        ProcessMapBuilder map = new(step);

        // Act
        KernelProcessStepInfo processMap = map.BuildStep();

        // Assert
        Assert.NotNull(processMap);
        Assert.IsType<KernelProcessMap>(processMap);
        Assert.Equal(map.Name, processMap.State.Name);
        Assert.Equal(map.Id, processMap.State.Id);
    }

    /// <summary>
    /// Verify <see cref="ProcessMapBuilder.BuildStep"/> throws an exception
    /// if the target is a <see cref="ProcessBuilder"/>> without the having
    /// <see cref="ProcessFunctionTargetBuilder.TargetEventId"/> defined.
    /// While this state should not be achievable by external callers, the
    /// underlying state contracts do permit this permutation.
    /// </summary>
    [Fact]
    public void ProcessMapBuilderFailsBuildForMapTarget()
    {
        // Arrange
        ProcessBuilder process = new(nameof(InvalidTestStep));
        ProcessStepBuilder step = process.AddStepFromType<SimpleTestStep>();
        ProcessFunctionTargetBuilder invalidTarget = new(new ProcessMapBuilder(step));

        // Act & Assert
        Assert.Throws<ArgumentException>(() => new ProcessMapBuilder(step).OnEvent("Test").SendEventTo(invalidTarget));
    }

    /// <summary>
    /// Verify <see cref="ProcessMapBuilder.BuildStep"/> throws an exception
    /// if the target is a <see cref="ProcessBuilder"/>> without the having
    /// <see cref="ProcessFunctionTargetBuilder.TargetEventId"/> defined.
    /// While this state should not be achievable by external callers, the
    /// underlying state contracts do permit this permutation.
    /// </summary>
    [Fact]
    public void ProcessMapBuilderFailsBuildForInvalidTarget()
    {
        // Arrange
        ProcessBuilder process = new(nameof(InvalidTestStep));
        ProcessStepBuilder step = process.AddStepFromType<SimpleTestStep>();

        // Act & Assert
        Assert.Throws<KernelException>(() => step.OnEvent("Test").SendEventTo(new ProcessFunctionTargetBuilder(new ProcessMapBuilder(step), "missing")));
    }

    private sealed class SimpleTestStep : KernelProcessStep<TestState>
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

    private sealed class InvalidTestStep : KernelProcessStep<TestState>
    {
        private TestState? _state;

        public override ValueTask ActivateAsync(KernelProcessStepState<TestState> state)
        {
            this._state = state.State;

            return ValueTask.CompletedTask;
        }

        [KernelFunction]
        public void TestFunction()
        {
            Assert.NotNull(this._state);
        }
    }

    private sealed class ComplexTestStep : KernelProcessStep<TestState>
    {
        private TestState? _state;

        public override ValueTask ActivateAsync(KernelProcessStepState<TestState> state)
        {
            this._state = state.State;

            return ValueTask.CompletedTask;
        }

        [KernelFunction]
        public void TestFunctionA(Guid value)
        {
            Assert.NotNull(this._state);
        }

        [KernelFunction]
        public void TestFunctionB(Guid value)
        {
            Assert.NotNull(this._state);
        }
    }

    private sealed class TestState
    {
        public Guid Value { get; set; }
    }
}
