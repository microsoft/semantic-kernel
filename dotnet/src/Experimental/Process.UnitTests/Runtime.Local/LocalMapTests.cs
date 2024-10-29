// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Xunit;

namespace Microsoft.SemanticKernel.Process.Runtime.Local.UnitTests;

/// <summary>
/// Unit tests for the <see cref="LocalMap"/> class.
/// </summary>
public class LocalMapTests
{
    /// <summary>
    /// Validates the <see cref="LocalMap"/> result as the first step in the process
    /// and with a step as the map operation.
    /// </summary>
    [Fact]
    public async Task ProcessMapResultAsFirstAsync()
    {
        // Arrange
        ProcessBuilder process = new(nameof(ProcessMapResultAsFirstAsync));

        ProcessStepBuilder computeStep = process.AddStepFromType<ComputeStep>();
        ProcessMapBuilder mapStep = process.AddMapForTarget(new ProcessFunctionTargetBuilder(computeStep));
        process
            .OnInputEvent("Start")
            .SendEventTo(mapStep);

        ProcessStepBuilder unionStep = process.AddStepFromType<UnionStep>();
        mapStep
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumFunction));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        await this.RunProcessAsync(kernel, processInstance, new int[] { 1, 2, 3, 4, 5 }, "Start");

        // Assert
        VerifyMapResult(kernel, UnionStep.ResultKey, 55L);
    }

    /// <summary>
    /// Validates the <see cref="LocalMap"/> result as the first step in the process
    /// and with a step as the map operation.
    /// </summary>
    [Fact]
    public async Task ProcessMapResultFilterEventAsync()
    {
        // Arrange
        ProcessBuilder process = new(nameof(ProcessMapResultFilterEventAsync));

        ProcessStepBuilder computeStep = process.AddStepFromType<ComputeStep>();
        ProcessMapBuilder mapStep = process.AddMapForTarget(new ProcessFunctionTargetBuilder(computeStep));
        process
            .OnInputEvent("Start")
            .SendEventTo(mapStep);

        ProcessStepBuilder unionStep = process.AddStepFromType<UnionStep>();
        mapStep
            .OnEvent(ComputeStep.CubicEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumFunction));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        await this.RunProcessAsync(kernel, processInstance, new int[] { 1, 2, 3, 4, 5 }, "Start");

        // Assert
        VerifyMapResult(kernel, UnionStep.ResultKey, 225L);
    }

    /// <summary>
    /// Validates the <see cref="LocalMap"/> result as the first step in the process
    /// and with a step as the map operation.
    /// </summary>
    [Fact]
    public async Task ProcessMapResultWithTransformAsync()
    {
        // Arrange
        ProcessBuilder process = new(nameof(ProcessMapResultWithTransformAsync));

        ProcessStepBuilder formatStep = process.AddStepFromType<FormatStep>();
        ProcessMapBuilder mapStep = process.AddMapForTarget(new ProcessFunctionTargetBuilder(formatStep));
        process
            .OnInputEvent("Start")
            .SendEventTo(mapStep);

        ProcessStepBuilder unionStep = process.AddStepFromType<UnionStep>();
        mapStep
            .OnEvent(FormatStep.EventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.JoinFunction));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        await this.RunProcessAsync(kernel, processInstance, new int[] { 1, 2, 3, 4, 5 }, "Start");

        // Assert
        VerifyMapResult(kernel, UnionStep.ResultKey, "[1]/[2]/[3]/[4]/[5]");
    }

    /// <summary>
    /// Validates the <see cref="LocalMap"/> result when the operation step
    /// contains multiple function targets.
    /// </summary>
    [Fact]
    public async Task ProcessMapResultOperationTargetAsync()
    {
        // Arrange
        ProcessBuilder process = new(nameof(ProcessMapResultOperationTargetAsync));

        ProcessStepBuilder computeStep = process.AddStepFromType<ComplexStep>();
        ProcessMapBuilder mapStep = process.AddMapForTarget(new ProcessFunctionTargetBuilder(computeStep, ComplexStep.ComputeFunction));

        process
            .OnInputEvent("Start")
            .SendEventTo(mapStep);

        ProcessStepBuilder unionStep = process.AddStepFromType<UnionStep>();
        mapStep
            .OnEvent(ComplexStep.ComputeEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumFunction));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        await this.RunProcessAsync(kernel, processInstance, new int[] { 1, 2, 3, 4, 5 }, "Start");

        // Assert
        VerifyMapResult(kernel, UnionStep.ResultKey, 55L);
    }

    /// <summary>
    /// Validates the <see cref="LocalMap"/> result as the second step in the process
    /// and with a step as the map operation.
    /// </summary>
    [Fact]
    public async Task ProcessMapResultAsTargetAsync()
    {
        // Arrange
        ProcessBuilder process = new(nameof(ProcessMapResultOperationTargetAsync));

        ProcessStepBuilder initStep = process.AddStepFromType<InitialStep>();
        process
            .OnInputEvent("Start")
            .SendEventTo(new ProcessFunctionTargetBuilder(initStep));

        ProcessStepBuilder computeStep = process.AddStepFromType<ComputeStep>();
        ProcessMapBuilder mapStep = process.AddMapForTarget(new ProcessFunctionTargetBuilder(computeStep));
        initStep
            .OnEvent(InitialStep.EventId)
            .SendEventTo(mapStep);

        ProcessStepBuilder unionStep = process.AddStepFromType<UnionStep>();
        mapStep
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumFunction));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        await this.RunProcessAsync(kernel, processInstance, new int[] { 1, 2, 3, 4, 5 }, "Start");

        // Assert
        VerifyMapResult(kernel, UnionStep.ResultKey, 55L);
    }

    /// <summary>
    /// Validates the <see cref="LocalMap"/> result responding to multiple events
    /// from a step as the map operation.
    /// </summary>
    [Fact]
    public async Task ProcessMapResultMultiEventAsync()
    {
        // Arrange
        ProcessBuilder process = new(nameof(ProcessMapResultMultiEventAsync));

        ProcessStepBuilder computeStep = process.AddStepFromType<ComputeStep>();
        ProcessMapBuilder mapStep = process.AddMapForTarget(new ProcessFunctionTargetBuilder(computeStep));
        process
            .OnInputEvent("Start")
            .SendEventTo(mapStep);

        ProcessStepBuilder unionSquaredStep = process.AddStepFromType<UnionStep, UnionState>(new() { Key = "Key1" });
        mapStep
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionSquaredStep, UnionStep.SumFunction));

        ProcessStepBuilder unionCubicStep = process.AddStepFromType<UnionStep, UnionState>(new() { Key = "Key2" });
        mapStep
            .OnEvent(ComputeStep.CubicEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionCubicStep, UnionStep.SumFunction));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        await this.RunProcessAsync(kernel, processInstance, new int[] { 1, 2, 3, 4, 5 }, "Start");

        // Assert
        VerifyMapResult(kernel, "Key1", 55L);
        VerifyMapResult(kernel, "Key2", 225L);
    }

    /// <summary>
    /// Validates the <see cref="LocalMap"/> result with a sub-process as the map operation.
    /// </summary>
    [Fact]
    public async Task ProcessMapResultProcessOperationAsync()
    {
        // Arrange
        ProcessBuilder process = new(nameof(ProcessMapResultProcessOperationAsync));

        ProcessBuilder mapProcess = new("MapOperation");
        ProcessStepBuilder computeStep = mapProcess.AddStepFromType<ComputeStep>();
        mapProcess
            .OnInputEvent("StartMap")
            .SendEventTo(new ProcessFunctionTargetBuilder(computeStep));

        ProcessMapBuilder mapStep = process.AddMapForTarget(mapProcess.WhereInputEventIs("StartMap"));
        process
            .OnInputEvent("Start")
            .SendEventTo(mapStep);

        ProcessStepBuilder unionStep = process.AddStepFromType<UnionStep>();
        mapStep
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumFunction));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        await this.RunProcessAsync(kernel, processInstance, new int[] { 1, 2, 3, 4, 5 }, "Start");

        // Assert
        VerifyMapResult(kernel, UnionStep.ResultKey, 55L);
    }

    /// <summary>
    /// Validates the <see cref="LocalMap"/> result even when an invalid edge is
    /// introduced to the map-operation.
    /// </summary>
    [Fact]
    public async Task ProcessMapResultWithTargetInvalidAsync()
    {
        // Arrange
        ProcessBuilder process = new(nameof(ProcessMapResultWithTargetInvalidAsync));

        //ProcessMapBuilder mapStep = process.AddMapFromType<ComputeStep>();
        ProcessStepBuilder computeStep = process.AddStepFromType<ComputeStep>();
        ProcessMapBuilder mapStep = process.AddMapForTarget(new ProcessFunctionTargetBuilder(computeStep));
        process
            .OnInputEvent("Start")
            .SendEventTo(mapStep);

        // CountStep is not part of the map operation, rather it has been defined on the "outer" process.
        ProcessStepBuilder countStep = process.AddStepFromType<CountStep>();
        computeStep
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(countStep));

        ProcessStepBuilder unionStep = process.AddStepFromType<UnionStep>();
        mapStep
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumFunction));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() => this.RunProcessAsync(kernel, processInstance, new int[] { 1, 2, 3, 4, 5 }, "Start"));
    }

    /// <summary>
    /// Validates the <see cref="LocalMap"/> result even when an invalid edge is
    /// introduced to the map-operation.
    /// </summary>
    [Fact]
    public async Task ProcessMapResultWithTargetExtraAsync()
    {
        // Arrange
        ProcessBuilder process = new(nameof(ProcessMapResultProcessOperationAsync));

        ProcessBuilder mapProcess = new("MapOperation");
        ProcessStepBuilder computeStep = mapProcess.AddStepFromType<ComputeStep>();
        mapProcess
            .OnInputEvent("Map")
            .SendEventTo(new ProcessFunctionTargetBuilder(computeStep));

        ProcessStepBuilder countStep = mapProcess.AddStepFromType<CountStep>();
        computeStep
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(countStep));

        ProcessMapBuilder mapStep = process.AddMapForTarget(mapProcess.WhereInputEventIs("Map"));
        process
            .OnInputEvent("Start")
            .SendEventTo(mapStep);

        ProcessStepBuilder unionStep = process.AddStepFromType<UnionStep>();
        mapStep
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumFunction));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        await this.RunProcessAsync(kernel, processInstance, new int[] { 1, 2, 3, 4, 5 }, "Start");

        // Assert
        VerifyMapResult(kernel, UnionStep.ResultKey, 55L);
        VerifyMapResult(kernel, CountStep.CountKey, 5);
    }

    /// <summary>
    /// Validates the <see cref="LocalMap"/> result as for a nested map operation.
    /// </summary>
    [Fact]
    public async Task ProcessMapResultForNestedMapAsync()
    {
        // Arrange
        ProcessBuilder process = new(nameof(ProcessMapResultForNestedMapAsync));

        ProcessBuilder mapProcess = new("MapOperation");
        ProcessStepBuilder computeStep = mapProcess.AddStepFromType<ComputeStep>();
        ProcessMapBuilder mapStepInner = mapProcess.AddMapForTarget(new ProcessFunctionTargetBuilder(computeStep));
        ProcessStepBuilder unionStepInner = mapProcess.AddStepFromType<UnionStep>();
        mapStepInner
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStepInner, UnionStep.SumFunction));

        mapProcess
            .OnInputEvent("StartMap")
            .SendEventTo(mapStepInner);

        ProcessMapBuilder mapStepOuter = process.AddMapForTarget(mapProcess.WhereInputEventIs("StartMap"));
        ProcessStepBuilder unionStepOuter = process.AddStepFromType<UnionStep>();
        mapStepOuter
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStepOuter, UnionStep.SumFunction));

        process
            .OnInputEvent("Start")
            .SendEventTo(mapStepOuter);

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        int[][] input =
        [
            [1, 2, 3, 4, 5],
            [1, 2, 3, 4, 5],
            [1, 2, 3, 4, 5],
        ];
        await this.RunProcessAsync(kernel, processInstance, input, "Start");

        // Assert
        VerifyMapResult(kernel, UnionStep.ResultKey, 165L);
    }

    private async Task RunProcessAsync(Kernel kernel, KernelProcess process, object? input, string inputEvent)
    {
        using LocalKernelProcessContext localProcess =
            await process.StartAsync(
                kernel,
                new KernelProcessEvent
                {
                    Id = inputEvent,
                    Data = input,
                });
    }

    private static void VerifyMapResult<TResult>(Kernel kernel, string resultKey, TResult expectedResult)
    {
        Assert.True(kernel.Data.ContainsKey(resultKey));
        Assert.NotNull(kernel.Data[resultKey]);
        Assert.IsType<TResult>(kernel.Data[resultKey]);
        Assert.Equal(expectedResult, kernel.Data[resultKey]);
    }

    /// <summary>
    /// A filler step used that emits the provided value as its output.
    /// </summary>
    private sealed class InitialStep : KernelProcessStep
    {
        public const string EventId = "Init";
        public const string InitFunction = "MapInit";

        [KernelFunction(InitFunction)]
        public async ValueTask InitAsync(KernelProcessStepContext context, object values)
        {
            await context.EmitEventAsync(new() { Id = EventId, Data = values });
        }
    }

    /// <summary>
    /// A step that contains a map operation that emits two events.
    /// </summary>
    private sealed class ComputeStep : KernelProcessStep
    {
        public const string SquareEventId = "SquareResult";
        public const string CubicEventId = "CubicResult";
        public const string ComputeFunction = "MapCompute";

        [KernelFunction(ComputeFunction)]
        public async ValueTask ComputeAsync(KernelProcessStepContext context, long value)
        {
            long square = value * value;
            await context.EmitEventAsync(new() { Id = SquareEventId, Data = square });
            await context.EmitEventAsync(new() { Id = CubicEventId, Data = square * value });
        }
    }

    /// <summary>
    /// A step that contains multiple functions, one of which is a map operation.
    /// </summary>
    private sealed class ComplexStep : KernelProcessStep
    {
        public const string ComputeEventId = "SquareResult";
        public const string ComputeFunction = "MapCompute";

        public const string OtherEventId = "CubicResult";
        public const string OtherFunction = "Other";

        [KernelFunction(ComputeFunction)]
        public async ValueTask ComputeAsync(KernelProcessStepContext context, long value)
        {
            long square = value * value;
            await context.EmitEventAsync(new() { Id = ComputeEventId, Data = square });
        }

        [KernelFunction(OtherFunction)]
        public async ValueTask OtherAsync(KernelProcessStepContext context)
        {
            await context.EmitEventAsync(new() { Id = OtherEventId });
        }
    }

    /// <summary>
    /// A map operation that formats the input as a string.
    /// </summary>
    private sealed class FormatStep : KernelProcessStep
    {
        public const string EventId = "FormatResult";
        public const string FormatFunction = "MapCompute";

        [KernelFunction(FormatFunction)]
        public async ValueTask FormatAsync(KernelProcessStepContext context, object value)
        {
            await context.EmitEventAsync(new() { Id = EventId, Data = $"[{value}]" });
        }
    }

    /// <summary>
    /// A step that contains a map operation that emits output that
    /// is not based on function input (perhaps simulating accessing a
    /// remote store)
    /// </summary>
    private sealed class QueryStep(ConcurrentQueue<string> store) : KernelProcessStep
    {
        public const string EventId = "QueryResult";
        public const string QueryFunction = "MapQuery";

        [KernelFunction(QueryFunction)]
        public async ValueTask QueryAsync(KernelProcessStepContext context)
        {
            string? value = null;
            int attempts = 0;
            do
            {
                ++attempts;
                store.TryDequeue(out value);
            } while (value == null && attempts < 3);

            if (value == null)
            {
                throw new InvalidDataException("Unable to query store");
            }

            await context.EmitEventAsync(new() { Id = EventId, Data = value });
        }
    }

    private sealed record UnionState
    {
        public string Key { get; set; } = UnionStep.ResultKey;
    };

    /// <summary>
    /// The step that combines the results of the map operation.
    /// </summary>
    private sealed class UnionStep : KernelProcessStep<UnionState>
    {
        public const string ResultKey = "Result";
        public const string EventId = "MapUnion";
        public const string SumFunction = "UnionSum";
        public const string JoinFunction = "UnionJoin";

        private UnionState _state = new();

        public override ValueTask ActivateAsync(KernelProcessStepState<UnionState> state)
        {
            this._state = state.State ?? throw new InvalidDataException();

            return ValueTask.CompletedTask;
        }

        [KernelFunction(SumFunction)]
        public async ValueTask SumAsync(KernelProcessStepContext context, IList<long> values, Kernel kernel)
        {
            long current = 0;
            long sum = values.Sum();
            if (kernel.Data.TryGetValue(this._state.Key, out object? result))
            {
                current = (long)result!;
            }
            kernel.Data[this._state.Key] = current + sum;
            await context.EmitEventAsync(new() { Id = EventId, Data = sum });
        }

        [KernelFunction(JoinFunction)]
        public async ValueTask JoinAsync(KernelProcessStepContext context, IList<string> values, Kernel kernel)
        {
            string list = string.Join("/", values);
            kernel.Data[this._state.Key] = list;
            await context.EmitEventAsync(new() { Id = EventId, Data = list });
        }
    }

    /// <summary>
    /// The step that counts how many times it has been invoked.
    /// </summary>
    private sealed class CountStep : KernelProcessStep
    {
        public const string CountFunction = nameof(Count);
        public const string CountKey = "Count";

        [KernelFunction]
        public void Count(Kernel kernel)
        {
            int count = 0;
            if (kernel.Data.TryGetValue(CountKey, out object? value))
            {
                count = (int)(value ?? 0);
            }
            kernel.Data[CountKey] = ++count;
        }
    }
}
