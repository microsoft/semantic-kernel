// Copyright (c) Microsoft. All rights reserved.
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

        ProcessMapBuilder mapStep = process.AddMapFromType<ComputeStep>();
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

        ProcessMapBuilder mapStep = process.AddMapFromType<ComputeStep>();
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

        ProcessMapBuilder mapStep = process.AddMapFromType<FormatStep>();
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

        ProcessMapBuilder mapStep = process.AddMapFromType<ComplexStep>().ForTarget(ComplexStep.ComputeFunction);
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

        ProcessMapBuilder mapStep = process.AddMapFromType<ComputeStep>();
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

        ProcessMapBuilder mapStep = process.AddMapFromType<ComputeStep>();
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
            .OnInputEvent("Map")
            .SendEventTo(new ProcessFunctionTargetBuilder(computeStep));

        ProcessMapBuilder mapStep = process.AddMapFromProcess(mapProcess, "Map");
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

    private async Task RunProcessAsync(Kernel kernel, KernelProcess process, object input, string inputEvent)
    {
        using LocalKernelProcessContext localProcess = // %%% LOGGER
            await process.StartAsync(
                kernel,
                new KernelProcessEvent
                {
                    Id = inputEvent,
                    Data = input
                });
    }

    private static void VerifyMapResult<TResult>(Kernel kernel, string resultKey, TResult expectedResult)
    {
        Assert.True(kernel.Data.ContainsKey(resultKey));
        Assert.NotNull(kernel.Data[resultKey]);
        Assert.IsType<TResult>(kernel.Data[resultKey]);
        Assert.Equal(expectedResult, kernel.Data[resultKey]);
    }

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

    private sealed record UnionState
    {
        public string Key { get; set; } = UnionStep.ResultKey;
    };

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
            long sum = values.Sum();
            kernel.Data[this._state.Key] = sum;
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
}
