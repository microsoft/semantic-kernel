// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using SemanticKernel.Process.TestsShared.Steps;
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

        ProcessMapBuilder mapStep = process.AddMapStepFromType<ComputeStep>();
        process
            .OnInputEvent("Start")
            .SendEventTo(new ProcessFunctionTargetBuilder(mapStep));

        ProcessStepBuilder unionStep = process.AddStepFromType<UnionStep>("Union");
        mapStep
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumSquareFunction));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        using LocalKernelProcessContext processContext = await this.RunProcessAsync(kernel, processInstance, new int[] { 1, 2, 3, 4, 5 }, "Start");

        // Assert
        UnionState unionState = await GetUnionStateAsync(processContext);
        Assert.Equal(55L, unionState.SquareResult);
    }

    /// <summary>
    /// Validates the <see cref="LocalMap"/> filtering on a specific event (cubic, not square).
    /// </summary>
    [Fact]
    public async Task ProcessMapResultFilterEventAsync()
    {
        // Arrange
        ProcessBuilder process = new(nameof(ProcessMapResultFilterEventAsync));

        ProcessMapBuilder mapStep = process.AddMapStepFromType<ComputeStep>();
        process
            .OnInputEvent("Start")
            .SendEventTo(new ProcessFunctionTargetBuilder(mapStep));

        ProcessStepBuilder unionStep = process.AddStepFromType<UnionStep>("Union");
        mapStep
            .OnEvent(ComputeStep.CubicEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumSquareFunction));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        using LocalKernelProcessContext processContext = await this.RunProcessAsync(kernel, processInstance, new int[] { 1, 2, 3, 4, 5 }, "Start");

        // Assert
        UnionState unionState = await GetUnionStateAsync(processContext);
        Assert.Equal(225L, unionState.SquareResult);
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

        ProcessMapBuilder mapStep = process.AddMapStepFromType<FormatStep>();
        process
            .OnInputEvent("Start")
            .SendEventTo(new ProcessFunctionTargetBuilder(mapStep));

        ProcessStepBuilder unionStep = process.AddStepFromType<UnionStep>("Union");
        mapStep
            .OnEvent(FormatStep.EventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.FormatFunction));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        using LocalKernelProcessContext processContext = await this.RunProcessAsync(kernel, processInstance, new int[] { 1, 2, 3, 4, 5 }, "Start");

        // Assert
        UnionState unionState = await GetUnionStateAsync(processContext);
        Assert.Equal("[1]/[2]/[3]/[4]/[5]", unionState.FormatResult);
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

        ProcessMapBuilder mapStep = process.AddMapStepFromType<ComplexStep>();
        process
            .OnInputEvent("Start")
            .SendEventTo(new ProcessFunctionTargetBuilder(mapStep, ComplexStep.ComputeFunction));

        ProcessStepBuilder unionStep = process.AddStepFromType<UnionStep>("Union");
        mapStep
            .OnEvent(ComplexStep.ComputeEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumSquareFunction));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        using LocalKernelProcessContext processContext = await this.RunProcessAsync(kernel, processInstance, new int[] { 1, 2, 3, 4, 5 }, "Start");

        // Assert
        UnionState unionState = await GetUnionStateAsync(processContext);
        Assert.Equal(55L, unionState.SquareResult);
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

        ProcessMapBuilder mapStep = process.AddMapStepFromType<ComputeStep>();
        initStep
            .OnEvent(InitialStep.EventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(mapStep));

        ProcessStepBuilder unionStep = process.AddStepFromType<UnionStep>("Union");
        mapStep
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumSquareFunction));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        using LocalKernelProcessContext processContext = await this.RunProcessAsync(kernel, processInstance, new int[] { 1, 2, 3, 4, 5 }, "Start");

        // Assert
        UnionState unionState = await GetUnionStateAsync(processContext);
        Assert.Equal(55L, unionState.SquareResult);
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

        ProcessMapBuilder mapStep = process.AddMapStepFromType<ComputeStep>();
        process
            .OnInputEvent("Start")
            .SendEventTo(new ProcessFunctionTargetBuilder(mapStep));

        ProcessStepBuilder unionStep = process.AddStepFromType<UnionStep>("Union");
        mapStep
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumSquareFunction));
        mapStep
            .OnEvent(ComputeStep.CubicEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumCubicFunction));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        using LocalKernelProcessContext processContext = await this.RunProcessAsync(kernel, processInstance, new int[] { 1, 2, 3, 4, 5 }, "Start");

        // Assert
        UnionState unionState = await GetUnionStateAsync(processContext);
        Assert.Equal(55L, unionState.SquareResult);
        Assert.Equal(225L, unionState.CubicResult);
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
            .OnInputEvent("Anything")
            .SendEventTo(new ProcessFunctionTargetBuilder(computeStep));

        ProcessMapBuilder mapStep = process.AddMapStepFromProcess(mapProcess);

        process
            .OnInputEvent("Start")
            .SendEventTo(mapStep.WhereInputEventIs("Anything"));

        ProcessStepBuilder unionStep = process.AddStepFromType<UnionStep>("Union");
        mapStep
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumSquareFunction));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        using LocalKernelProcessContext processContext = await this.RunProcessAsync(kernel, processInstance, new int[] { 1, 2, 3, 4, 5 }, "Start");

        // Assert
        UnionState unionState = await GetUnionStateAsync(processContext);
        Assert.Equal(55L, unionState.SquareResult);
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

        ProcessMapBuilder mapStep = process.AddMapStepFromType<ComputeStep>();
        process
            .OnInputEvent("Start")
            .SendEventTo(new ProcessFunctionTargetBuilder(mapStep));

        // CountStep is not part of the map operation, rather it has been defined on the "outer" process.
        CommonSteps.CountStep.Index = 0; // Reset static state (test hack)
        ProcessStepBuilder countStep = process.AddStepFromType<CommonSteps.CountStep>();
        mapStep.MapOperation
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(countStep));

        ProcessStepBuilder unionStep = process.AddStepFromType<UnionStep>("Union");
        mapStep
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumSquareFunction));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() => this.RunProcessAsync(kernel, processInstance, new int[] { 1, 2, 3, 4, 5 }, "Start"));
    }

    /// <summary>
    /// Validates the <see cref="LocalMap"/> result an extra edge is
    /// introduced to the map-operation.
    /// </summary>
    [Fact]
    public async Task ProcessMapResultWithTargetExtraAsync()
    {
        // Arrange
        CommonSteps.CountStep.Index = 0;
        ProcessBuilder process = new(nameof(ProcessMapResultProcessOperationAsync));

        ProcessBuilder mapProcess = new("MapOperation");
        ProcessStepBuilder computeStep = mapProcess.AddStepFromType<ComputeStep>();
        mapProcess
            .OnInputEvent("Anything")
            .SendEventTo(new ProcessFunctionTargetBuilder(computeStep));

        ProcessStepBuilder countStep = mapProcess.AddStepFromType<CommonSteps.CountStep>();
        computeStep
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(countStep));

        ProcessMapBuilder mapStep = process.AddMapStepFromProcess(mapProcess);
        process
            .OnInputEvent("Start")
            .SendEventTo(mapStep.WhereInputEventIs("Anything"));

        ProcessStepBuilder unionStep = process.AddStepFromType<UnionStep>("Union");
        mapStep
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumSquareFunction));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        using LocalKernelProcessContext processContext = await this.RunProcessAsync(kernel, processInstance, new int[] { 1, 2, 3, 4, 5 }, "Start");

        // Assert
        UnionState unionState = await GetUnionStateAsync(processContext);
        Assert.Equal(55L, unionState.SquareResult);
        Assert.Equal(5, CommonSteps.CountStep.Index);
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
        ProcessMapBuilder mapStepInner = mapProcess.AddMapStepFromType<ComputeStep>();
        ProcessStepBuilder unionStepInner = mapProcess.AddStepFromType<UnionStep>();
        mapStepInner
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStepInner, UnionStep.SumSquareFunction));

        mapProcess
            .OnInputEvent("Anything")
            .SendEventTo(new ProcessFunctionTargetBuilder(mapStepInner));

        ProcessMapBuilder mapStepOuter = process.AddMapStepFromProcess(mapProcess);
        ProcessStepBuilder unionStepOuter = process.AddStepFromType<UnionStep>("Union");
        mapStepOuter
            .OnEvent(UnionStep.EventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStepOuter, UnionStep.SumSquareFunction));

        process
            .OnInputEvent("Start")
            .SendEventTo(mapStepOuter.WhereInputEventIs("Anything"));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        int[][] input =
        [
            [1, 2, 3, 4, 5],
            [1, 2, 3, 4, 5],
            [1, 2, 3, 4, 5],
        ];
        using LocalKernelProcessContext processContext = await this.RunProcessAsync(kernel, processInstance, input, "Start");

        // Assert
        UnionState unionState = await GetUnionStateAsync(processContext);
        Assert.Equal(165L, unionState.SquareResult);
    }

    private async Task<LocalKernelProcessContext> RunProcessAsync(Kernel kernel, KernelProcess process, object? input, string inputEvent)
    {
        return
            await process.StartAsync(
                kernel,
                new KernelProcessEvent
                {
                    Id = inputEvent,
                    Data = input,
                });
    }

    private static async Task<UnionState> GetUnionStateAsync(LocalKernelProcessContext processContext)
    {
        KernelProcess processState = await processContext.GetStateAsync();
        KernelProcessStepState<UnionState> unionState = (KernelProcessStepState<UnionState>)processState.Steps.Single(s => s.State.Name == "Union").State;
        Assert.NotNull(unionState);
        Assert.NotNull(unionState.State);
        return unionState.State;
    }

    /// <summary>
    /// A filler step used that emits the provided value as its output.
    /// </summary>
    private sealed class IncrementStep : KernelProcessStep
    {
        public const string EventId = "Bump";
        public const string IncrementFunction = "Increment";

        [KernelFunction(IncrementFunction)]
        public async ValueTask IncrementAsync(KernelProcessStepContext context, int count)
        {
            await context.EmitEventAsync(new() { Id = EventId, Data = count + 1, Visibility = KernelProcessEventVisibility.Public });
        }
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
            await context.EmitEventAsync(new() { Id = EventId, Data = values, Visibility = KernelProcessEventVisibility.Public });
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
            await context.EmitEventAsync(new() { Id = SquareEventId, Data = square, Visibility = KernelProcessEventVisibility.Public });
            await context.EmitEventAsync(new() { Id = CubicEventId, Data = square * value, Visibility = KernelProcessEventVisibility.Public });
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

    private sealed record UnionState
    {
        public long SquareResult { get; set; }
        public long CubicResult { get; set; }
        public string FormatResult { get; set; } = string.Empty;
    };

    /// <summary>
    /// The step that combines the results of the map operation.
    /// </summary>
    private sealed class UnionStep : KernelProcessStep<UnionState>
    {
        public const string EventId = "MapUnion";
        public const string SumSquareFunction = "UnionSquare";
        public const string SumCubicFunction = "UnionCubic";
        public const string FormatFunction = "UnionFormat";

        private UnionState _state = new();

        public override ValueTask ActivateAsync(KernelProcessStepState<UnionState> state)
        {
            this._state = state.State ?? throw new InvalidDataException();

            return ValueTask.CompletedTask;
        }

        [KernelFunction(SumSquareFunction)]
        public async ValueTask SumSquareAsync(KernelProcessStepContext context, IList<long> values)
        {
            this._state.SquareResult = values.Sum();
            await context.EmitEventAsync(new() { Id = EventId, Data = this._state.SquareResult });
        }

        [KernelFunction(SumCubicFunction)]
        public async ValueTask SumCubicAsync(KernelProcessStepContext context, IList<long> values)
        {
            this._state.CubicResult = values.Sum();
            await context.EmitEventAsync(new() { Id = EventId, Data = this._state.CubicResult });
        }

        [KernelFunction(FormatFunction)]
        public void FormatValues(IList<string> values)
        {
            this._state.FormatResult = string.Join("/", values);
        }
    }
}
